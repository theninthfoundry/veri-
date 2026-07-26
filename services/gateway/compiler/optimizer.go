package compiler

import (
	"fmt"
	"strings"
	"time"
)

type OptimizationNode struct {
	ID         string                 `json:"id"`
	Kind       string                 `json:"kind"`
	Label      string                 `json:"label"`
	Content    map[string]interface{} `json:"content"`
	Confidence float64                `json:"confidence"`
	Latency    float64                `json:"latency"`
	Cost       float64                `json:"cost"`
	Tokens     map[string]int         `json:"tokens"`
}

type OptimizationEdge struct {
	ID       string `json:"id"`
	SourceID string `json:"source_id"`
	TargetID string `json:"target_id"`
	Kind     string `json:"kind"`
}

type OptimizationRequest struct {
	SessionID string             `json:"session_id"`
	Nodes     []OptimizationNode `json:"nodes"`
	Edges     []OptimizationEdge `json:"edges"`
}

type OptimizationResult struct {
	SessionID        string             `json:"session_id"`
	OriginalNodeCount int                `json:"original_node_count"`
	OptimizedNodeCount int               `json:"optimized_node_count"`
	PrunedNodes      int                `json:"pruned_nodes"`
	MergedToolCalls  int                `json:"merged_tool_calls"`
	EstimatedCostSaved float64          `json:"estimated_cost_saved"`
	EstimatedTokensSaved int            `json:"estimated_tokens_saved"`
	OptimizedNodes   []OptimizationNode `json:"optimized_nodes"`
	OptimizedEdges   []OptimizationEdge `json:"optimized_edges"`
	Timestamp        string             `json:"timestamp"`
}

// GraphOptimizer performs static analysis and optimization over agent execution graphs.
type GraphOptimizer struct{}

func NewGraphOptimizer() *GraphOptimizer {
	return &GraphOptimizer{}
}

func (goOpt *GraphOptimizer) Optimize(req OptimizationRequest) OptimizationResult {
	startNodes := len(req.Nodes)
	prunedCount := 0
	mergedCount := 0
	tokensSaved := 0
	costSaved := 0.0

	// 1. Reasoning Pruner Pass: Remove orphaned error/abandoned reasoning nodes
	validNodes := make([]OptimizationNode, 0)
	errorNodeIDs := make(map[string]bool)

	for _, n := range req.Nodes {
		if n.Kind == "error" || strings.Contains(strings.ToLower(n.Label), "error") {
			errorNodeIDs[n.ID] = true
			prunedCount++
			tokensSaved += 150
			costSaved += 0.002
		} else {
			validNodes = append(validNodes, n)
		}
	}

	// 2. Tool Call Merger Pass: Merge identical consecutive tool_invocation calls
	mergedNodes := make([]OptimizationNode, 0)
	toolSeen := make(map[string]int)

	for _, n := range validNodes {
		if n.Kind == "tool_invocation" || n.Kind == "action" {
			key := fmt.Sprintf("%s:%v", n.Label, n.Content["query"])
			if idx, found := toolSeen[key]; found {
				// Deduplicate tool call
				mergedNodes[idx].Latency += n.Latency
				mergedCount++
				tokensSaved += 200
				costSaved += 0.003
				continue
			}
			toolSeen[key] = len(mergedNodes)
		}
		mergedNodes = append(mergedNodes, n)
	}

	// Filter Edges to only valid nodes
	nodeMap := make(map[string]bool)
	for _, n := range mergedNodes {
		nodeMap[n.ID] = true
	}

	validEdges := make([]OptimizationEdge, 0)
	for _, e := range req.Edges {
		if nodeMap[e.SourceID] && nodeMap[e.TargetID] {
			validEdges = append(validEdges, e)
		}
	}

	return OptimizationResult{
		SessionID:          req.SessionID,
		OriginalNodeCount:  startNodes,
		OptimizedNodeCount: len(mergedNodes),
		PrunedNodes:        prunedCount,
		MergedToolCalls:    mergedCount,
		EstimatedCostSaved: costSaved,
		EstimatedTokensSaved: tokensSaved,
		OptimizedNodes:     mergedNodes,
		OptimizedEdges:     validEdges,
		Timestamp:          time.Now().Format(time.RFC3339),
	}
}
