Your task is to translate this visual flowchart into a strict ELK (Eclipse Layout Kernel) JSON format for a 3D-printing pipeline.

---

# Global Layout Rules:
Start the JSON with the following exact root configuration to enforce 90-degree Manhattan routing and fixed ports:

        {
        "id": "root",
        "layoutOptions": {
            "elk.algorithm": "layered",
            "elk.direction": "DOWN",
            "elk.edgeRouting": "ORTHOGONAL",
            "elk.spacing.nodeNode": "80",
            "elk.layered.spacing.nodeNodeBetweenLayers": "80",
            "elk.spacing.edgeNode": "80",
            "elk.layered.spacing.edgeNodeBetweenLayers": "80",
            "elk.layered.layering.strategy": "INTERACTIVE",
            "elk.layered.cycleBreaking.strategy": "DEPTH_FIRST",
            "elk.portConstraints": "FIXED_SIDE"
        },
        "children": [],
        "edges": []
        }

---

# Node Definition Rules (The children array):
For every shape in the flowchart, create a node object. You MUST include a custom "myCustomShape" attribute and assign sizes and ports exactly as follows:

1. Start/Finish Nodes (Circles/Ovals):

        "myCustomShape": "circle"

        "width": 40, "height": 40
        
                Crucial Rule: Nodes with side ports MUST include "layoutOptions": { "elk.portConstraints": "FIXED_SIDE" } inside the node definition.

        Ports: Start nodes need a SOUTH port. Finish nodes need a NORTH port. (if two or more ports arrive at the finish node merge them in the north port)

2. Process/Action Nodes (Rectangles):

        "myCustomShape": "square"

        "width": 40, "height": 40
        
                Crucial Rule: Nodes with side ports MUST include "layoutOptions": { "elk.portConstraints": "FIXED_SIDE" } inside the node definition.

        Ports: either NORTH, EAST or WEST (for incoming), SOUTH (for outgoing).

3. Input/Output Nodes (Trapezoid):

        "myCustomShape": "trapezoid"

        "width": 50, "height": 50
        
                Crucial Rule: Nodes with side ports MUST include "layoutOptions": { "elk.portConstraints": "FIXED_SIDE" } inside the node definition.

        Ports: either NORTH, EAST or WEST (for incoming), SOUTH (for outgoing).


4. Decision Nodes (Diamonds):

        "myCustomShape": "diamond"

        "width": 60, "height": 60

        Crucial Rule: Nodes with side ports MUST include "layoutOptions": { "elk.portConstraints": "FIXED_SIDE" } inside the node definition.

        Ports: NORTH (incoming), SOUTH (the "Yes"/Main flow), and either EAST or WEST (for the "No"/Bypass flow).
        
5. Ranking and Layering:
To ensure nodes are positioned in the correct vertical rank relative to the flowchart's flow:

    Assign a "layoutOptions": { "elk.layered.layering.layer": "X" } to each node.

    The top-most node (Start) should be layer 0.

    Each subsequent step down the flowchart should increment the layer number (e.g., 1, 2, 3).

    Nodes that appear side-by-side (like the RIGHT or LEFT branch of a decision node) should typically share the same layer number as the node they are logically aligned with.
        
      
      
## Node Labels:
For every node, you MUST include a labels array containing the text found inside the shape in the flowchart.

Syntax: "labels": [{ "text": "Node Text Here" }]

Place this inside the node object alongside id and myCustomShape.
        
        
## Port Syntax:
Ports must be defined strictly like this:
        {"id": "nodeName_out_south", "layoutOptions": { "elk.port.side": "SOUTH" }}

---

#Edge Definition Rules (The edges array):
Trace every line in the flowchart.

    Define "source" and "target" node IDs.

    You MUST explicitly map the "sourcePort" and "targetPort".

    Vertical center flow should go SOUTH to NORTH.

    Bypass loops (like "No" branches) MUST exit an EAST or WEST port and enter a NORTH port to prevent overlapping the central spine.

    If a line has text (like "Yes" or "No"), add it to the edge: "labels": [{"text": "Yes"}].
    
    if two or more edge arrive at the same node merge them in a single port.
    
    Strict Port Uniqueness: A single port (ID) cannot function as both a sourcePort and a targetPort within the same JSON.

    Collision Avoidance: If an edge exits a node's EAST port, no incoming edge can target that same node's EAST port.
    
---

#Port Conflict Logic:

Before generating, verify: Is any port ID used in both the "source" of one edge and the "target" of another? If yes, move the incoming edge to an unused cardinal side (WEST or NORTH).
     
    
---

Output ONLY the raw, valid JSON. Do not include markdown formatting, explanations, or conversational filler.
