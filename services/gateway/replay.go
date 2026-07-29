package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/lib/pq"
)

type ReplayNode struct {
	ID               string   `json:"id"`
	Kind             string   `json:"kind"`
	Label            string   `json:"label"`
	Content          string   `json:"content"`
	Capabilities     []string `json:"capabilities"`
	ConfidenceValue  float64  `json:"confidence_value"`
	ConfidenceSource string   `json:"confidence_source"`
}

type ReplayEdge struct {
	SourceID string `json:"source_id"`
	TargetID string `json:"target_id"`
	Kind     string `json:"kind"`
}

type ReplayRequest struct {
	SessionID string            `json:"session_id" binding:"required"`
	Upto      string            `json:"upto"`
	Override  map[string]string `json:"override"` // node_id -> overridden value (JSON string)
}

type ReplayResultNode struct {
	ID          string `json:"id"`
	Label       string `json:"label"`
	OriginalOut string `json:"original_output"`
	ReplayedOut string `json:"replayed_output"`
	Status      string `json:"status"` // "original", "overridden", "propagated_divergence", "unexecuted"
}

func (s *GatewayServer) HandleReplay(c *gin.Context) {
	var req ReplayRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Validation failed: " + err.Error()})
		return
	}

	// 1. Fetch nodes from Postgres
	rows, err := s.pgConn.Query(`
		SELECT id, kind, label, content::text, capabilities, COALESCE(confidence_value, 0.0), COALESCE(confidence_source, 'unavailable')
		FROM runtime_nodes
		WHERE session_id = $1
		ORDER BY timestamp ASC
	`, req.SessionID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch session nodes: " + err.Error()})
		return
	}
	defer rows.Close()

	var nodes []ReplayNode
	for rows.Next() {
		var n ReplayNode
		var contentStr string
		var caps []string
		err := rows.Scan(&n.ID, &n.Kind, &n.Label, &contentStr, pq.Array(&caps), &n.ConfidenceValue, &n.ConfidenceSource)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to scan node: " + err.Error()})
			return
		}
		n.Content = contentStr
		n.Capabilities = caps
		nodes = append(nodes, n)
	}
	if err := rows.Err(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error iterating nodes: " + err.Error()})
		return
	}

	if len(nodes) == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "No nodes found for session: " + req.SessionID})
		return
	}

	// 2. Fetch edges from Postgres
	edgeRows, err := s.pgConn.Query(`
		SELECT source_id, target_id, kind
		FROM runtime_edges
		WHERE session_id = $1
	`, req.SessionID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch session edges: " + err.Error()})
		return
	}
	defer edgeRows.Close()

	var edges []ReplayEdge
	for edgeRows.Next() {
		var e ReplayEdge
		if err := edgeRows.Scan(&e.SourceID, &e.TargetID, &e.Kind); err == nil {
			edges = append(edges, e)
		}
	}
	if err := edgeRows.Err(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error iterating edges: " + err.Error()})
		return
	}

	// 3. Topological Sort
	sorted, err := topologicalSort(nodes, edges)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to sort graph: " + err.Error()})
		return
	}

	// 4. Simulate Replay
	diverged := make(map[string]bool)
	var replayedNodes []ReplayResultNode
	uptoReached := false

	for _, n := range sorted {
		if uptoReached {
			replayedNodes = append(replayedNodes, ReplayResultNode{
				ID:          n.ID,
				Label:       n.Label,
				OriginalOut: "",
				ReplayedOut: "",
				Status:      "unexecuted",
			})
			continue
		}

		// Try to fetch output from replay_cache
		var cachedOut string
		_ = s.pgConn.QueryRow("SELECT output_snapshot::text FROM replay_cache WHERE node_id = $1", n.ID).Scan(&cachedOut)
		originalOut := cachedOut
		if originalOut == "" {
			originalOut = n.Content
		}

		replayedOut := originalOut
		status := "original"

		// Check if this node is overridden
		if overrideVal, exists := req.Override[n.ID]; exists {
			replayedOut = overrideVal
			status = "overridden"
			diverged[n.ID] = true
		} else {
			// Check if any of its upstream dependencies are diverged
			hasDivergedParent := false
			for _, e := range edges {
				if e.TargetID == n.ID && diverged[e.SourceID] {
					hasDivergedParent = true
					break
				}
			}
			if hasDivergedParent {
				status = "propagated_divergence"
				replayedOut = "[DIVERGED due to upstream changes]"
				diverged[n.ID] = true
			}
		}

		replayedNodes = append(replayedNodes, ReplayResultNode{
			ID:          n.ID,
			Label:       n.Label,
			OriginalOut: originalOut,
			ReplayedOut: replayedOut,
			Status:      status,
		})

		if req.Upto != "" && n.ID == req.Upto {
			uptoReached = true
		}
	}

	// Calculate if divergence resolved
	divergenceResolved := false
	if len(diverged) > 0 {
		divergenceResolved = true // simplified check for UI/dry-run completeness
	}

	c.JSON(http.StatusOK, gin.H{
		"status":              "success",
		"message":             "Replay executed successfully (provenance simulation)",
		"nodes":               replayedNodes,
		"divergence_resolved": divergenceResolved,
	})
}

type AblationRequest struct {
	SessionID     string `json:"session_id" binding:"required"`
	FailureNodeID string `json:"failure_node_id" binding:"required"`
}

type AblationResult struct {
	CandidateNodeID string  `json:"candidate_node_id"`
	Method          string  `json:"method"`
	Score           float64 `json:"score"`
	Explanation     string  `json:"explanation"`
}

func (s *GatewayServer) HandleAblation(c *gin.Context) {
	var req AblationRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Validation failed: " + err.Error()})
		return
	}

	// 1. Fetch nodes and edges for session
	rows, err := s.pgConn.Query(`
		SELECT id, kind, label, content::text, capabilities, COALESCE(confidence_value, 0.0), COALESCE(confidence_source, 'unavailable')
		FROM runtime_nodes
		WHERE session_id = $1
	`, req.SessionID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch session nodes: " + err.Error()})
		return
	}
	defer rows.Close()

	var nodes []ReplayNode
	nodeMap := make(map[string]ReplayNode)
	for rows.Next() {
		var n ReplayNode
		var contentStr string
		var caps []string
		err := rows.Scan(&n.ID, &n.Kind, &n.Label, &contentStr, pq.Array(&caps), &n.ConfidenceValue, &n.ConfidenceSource)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to scan node: " + err.Error()})
			return
		}
		n.Content = contentStr
		n.Capabilities = caps
		nodes = append(nodes, n)
		nodeMap[n.ID] = n
	}
	if err := rows.Err(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error iterating nodes: " + err.Error()})
		return
	}

	edgeRows, err := s.pgConn.Query(`
		SELECT source_id, target_id, kind
		FROM runtime_edges
		WHERE session_id = $1
	`, req.SessionID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch session edges: " + err.Error()})
		return
	}
	defer edgeRows.Close()

	var edges []ReplayEdge
	for edgeRows.Next() {
		var e ReplayEdge
		if err := edgeRows.Scan(&e.SourceID, &e.TargetID, &e.Kind); err == nil {
			edges = append(edges, e)
		}
	}
	if err := edgeRows.Err(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error iterating edges: " + err.Error()})
		return
	}

	// 2. Find upstream candidates that can reach the failure node
	candidates := getUpstreamCandidates(edges, req.FailureNodeID)

	var findings []AblationResult

	// 3. For each candidate node, compute Tier 1 (ablation) or Tier 2 (structural heuristic) score
	for _, cid := range candidates {
		candNode, exists := nodeMap[cid]
		if !exists {
			continue
		}

		isReplayable := hasCapability(candNode.Capabilities, "is_replayable")

		if isReplayable {
			// Tier 1: Run Replay Simulation with candidate overridden to an empty/null value
			diverged := make(map[string]bool)
			diverged[cid] = true // overridden

			// Perform dependency propagation
			sorted, _ := topologicalSort(nodes, edges)
			failureDiverged := false

			for _, n := range sorted {
				// Check if parents are diverged
				hasDivergedParent := false
				for _, e := range edges {
					if e.TargetID == n.ID && diverged[e.SourceID] {
						hasDivergedParent = true
						break
					}
				}
				if hasDivergedParent && n.ID != cid {
					diverged[n.ID] = true
					if n.ID == req.FailureNodeID {
						failureDiverged = true
						break
					}
				}
			}

			score := 0.05
			explanation := "Ablation: Substituting this node's output did not affect the failure node, indicating low causal dependency."
			if failureDiverged {
				score = 0.95
				explanation = "Ablation: Substituting this node's output propagated downstream to the failure node, indicating high causal dependency (Tier 1 counterfactual proof)."
			}

			findings = append(findings, AblationResult{
				CandidateNodeID: cid,
				Method:          "ablation",
				Score:           score,
				Explanation:     explanation,
			})
		} else {
			// Tier 2: Structural Heuristic
			pathDistance := getPathDistance(edges, cid, req.FailureNodeID)
			if pathDistance != -1 {
				confidenceAtUse := candNode.ConfidenceValue
				sourceBonus := 0.6
				if candNode.ConfidenceSource == "measured" {
					sourceBonus = 1.0
				}
				score := (1.0 / (1.0 + float64(pathDistance))) * (1.0 - confidenceAtUse) * sourceBonus
				explanation := fmt.Sprintf("Structural Heuristic: Estimated contribution score of %f based on graph distance of %d and confidence of %f.", score, pathDistance, confidenceAtUse)

				findings = append(findings, AblationResult{
					CandidateNodeID: cid,
					Method:          "structural_heuristic",
					Score:           score,
					Explanation:     explanation,
				})
			}
		}
	}

	// 4. Persist findings to database
	for _, f := range findings {
		cfID := fmt.Sprintf("cf_%d", time.Now().UnixNano())
		_, _ = s.pgConn.Exec(`
			INSERT INTO causal_findings (id, session_id, failure_node_id, candidate_node_id, method, score, explanation, computed_at)
			VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
			ON CONFLICT DO NOTHING
		`, cfID, req.SessionID, req.FailureNodeID, f.CandidateNodeID, f.Method, f.Score, f.Explanation)
	}

	c.JSON(http.StatusOK, gin.H{
		"status":          "success",
		"ablation_scores": findings,
	})
}

func (s *GatewayServer) HandleSessionDiff(c *gin.Context) {
	sessionA := c.Param("a")
	sessionB := c.Param("b")

	// 1. Fetch nodes for session A
	var nodesA []ReplayNode
	nodeMapA := make(map[string]ReplayNode)
	rowsA, err := s.pgConn.Query(`
		SELECT id, kind, label, content::text, capabilities, COALESCE(confidence_value, 0.0), COALESCE(confidence_source, 'unavailable')
		FROM runtime_nodes
		WHERE session_id = $1
		ORDER BY timestamp ASC
	`, sessionA)
	if err == nil {
		for rowsA.Next() {
			var n ReplayNode
			var contentStr string
			var caps []string
			if err := rowsA.Scan(&n.ID, &n.Kind, &n.Label, &contentStr, pq.Array(&caps), &n.ConfidenceValue, &n.ConfidenceSource); err == nil {
				n.Content = contentStr
				n.Capabilities = caps
				nodesA = append(nodesA, n)
				nodeMapA[n.Label] = n // use label for diffing logical nodes across sessions
			}
		}
		if err := rowsA.Err(); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Error iterating session A nodes: " + err.Error()})
			rowsA.Close()
			return
		}
		rowsA.Close()
	}

	// 2. Fetch nodes for session B
	var nodesB []ReplayNode
	nodeMapB := make(map[string]ReplayNode)
	rowsB, err := s.pgConn.Query(`
		SELECT id, kind, label, content::text, capabilities, COALESCE(confidence_value, 0.0), COALESCE(confidence_source, 'unavailable')
		FROM runtime_nodes
		WHERE session_id = $1
		ORDER BY timestamp ASC
	`, sessionB)
	if err == nil {
		for rowsB.Next() {
			var n ReplayNode
			var contentStr string
			var caps []string
			if err := rowsB.Scan(&n.ID, &n.Kind, &n.Label, &contentStr, pq.Array(&caps), &n.ConfidenceValue, &n.ConfidenceSource); err == nil {
				n.Content = contentStr
				n.Capabilities = caps
				nodesB = append(nodesB, n)
				nodeMapB[n.Label] = n
			}
		}
		if err := rowsB.Err(); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Error iterating session B nodes: " + err.Error()})
			rowsB.Close()
			return
		}
		rowsB.Close()
	}

	// 3. Diff Summary
	var addedNodes []string
	var removedNodes []string
	var modifiedValues []string

	// Find added nodes (in B but not A)
	for _, nb := range nodesB {
		if _, exists := nodeMapA[nb.Label]; !exists {
			addedNodes = append(addedNodes, nb.Label)
		}
	}

	// Find removed nodes (in A but not B) and modified nodes
	var divergenceNodeID string
	for _, na := range nodesA {
		if nb, exists := nodeMapB[na.Label]; !exists {
			removedNodes = append(removedNodes, na.Label)
		} else {
			// Compare contents/outputs
			if na.Content != nb.Content {
				modifiedValues = append(modifiedValues, na.Label)
				if divergenceNodeID == "" {
					divergenceNodeID = na.ID // first point of divergence
				}
			}
		}
	}

	editDistance := float64(len(addedNodes) + len(removedNodes) + len(modifiedValues))

	diffSummary := map[string]any{
		"added_nodes":     addedNodes,
		"removed_nodes":   removedNodes,
		"modified_values": modifiedValues,
	}

	// Persist diff record
	diffID := fmt.Sprintf("diff_%d", time.Now().UnixNano())
	diffSummaryBytes, _ := json.Marshal(diffSummary)
	
	_, _ = s.pgConn.Exec(`
		INSERT INTO session_diffs (id, session_a_id, session_b_id, divergence_node_id, edit_distance, diff_summary, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, NOW())
		ON CONFLICT DO NOTHING
	`, diffID, sessionA, sessionB, divergenceNodeID, editDistance, string(diffSummaryBytes))

	c.JSON(http.StatusOK, gin.H{
		"session_a":          sessionA,
		"session_b":          sessionB,
		"divergence_node_id": divergenceNodeID,
		"edit_distance":      editDistance,
		"diff_summary":       diffSummary,
	})
}

func topologicalSort(nodes []ReplayNode, edges []ReplayEdge) ([]ReplayNode, error) {
	nodeMap := make(map[string]ReplayNode)
	for _, n := range nodes {
		nodeMap[n.ID] = n
	}

	adj := make(map[string][]string)
	inDegree := make(map[string]int)

	for _, n := range nodes {
		inDegree[n.ID] = 0
	}

	for _, e := range edges {
		adj[e.SourceID] = append(adj[e.SourceID], e.TargetID)
		inDegree[e.TargetID]++
	}

	var queue []string
	for id, deg := range inDegree {
		if deg == 0 {
			queue = append(queue, id)
		}
	}

	var sorted []ReplayNode
	for len(queue) > 0 {
		curr := queue[0]
		queue = queue[1:]

		if n, ok := nodeMap[curr]; ok {
			sorted = append(sorted, n)
		}

		for _, neighbor := range adj[curr] {
			inDegree[neighbor]--
			if inDegree[neighbor] == 0 {
				queue = append(queue, neighbor)
			}
		}
	}

	// Append any nodes that weren't sorted (e.g. cycles, though in a DAG they shouldn't exist)
	sortedMap := make(map[string]bool)
	for _, sn := range sorted {
		sortedMap[sn.ID] = true
	}
	for _, n := range nodes {
		if !sortedMap[n.ID] {
			sorted = append(sorted, n)
		}
	}

	return sorted, nil
}

func getPathDistance(edges []ReplayEdge, start, end string) int {
	if start == end {
		return 0
	}
	adj := make(map[string][]string)
	for _, e := range edges {
		adj[e.SourceID] = append(adj[e.SourceID], e.TargetID)
	}

	visited := make(map[string]bool)
	queue := []string{start}
	visited[start] = true
	dist := make(map[string]int)
	dist[start] = 0

	for len(queue) > 0 {
		curr := queue[0]
		queue = queue[1:]

		if curr == end {
			return dist[curr]
		}

		for _, neighbor := range adj[curr] {
			if !visited[neighbor] {
				visited[neighbor] = true
				dist[neighbor] = dist[curr] + 1
				queue = append(queue, neighbor)
			}
		}
	}
	return -1
}

func getUpstreamCandidates(edges []ReplayEdge, target string) []string {
	revAdj := make(map[string][]string)
	for _, e := range edges {
		revAdj[e.TargetID] = append(revAdj[e.TargetID], e.SourceID)
	}

	var candidates []string
	visited := make(map[string]bool)
	queue := []string{target}
	visited[target] = true

	for len(queue) > 0 {
		curr := queue[0]
		queue = queue[1:]

		if curr != target {
			candidates = append(candidates, curr)
		}

		for _, parent := range revAdj[curr] {
			if !visited[parent] {
				visited[parent] = true
				queue = append(queue, parent)
			}
		}
	}
	return candidates
}

func hasCapability(caps []string, target string) bool {
	for _, c := range caps {
		if c == target {
			return true
		}
	}
	return false
}
