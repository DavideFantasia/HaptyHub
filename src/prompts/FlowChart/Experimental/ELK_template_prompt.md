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
            "elk.spacing.nodeNode": "30",
            "elk.layered.spacing.nodeNodeBetweenLayers": "40",
            "elk.spacing.edgeNode": "40",
            "elk.layered.spacing.edgeNodeBetweenLayers": "40",
            "elk.layered.layering.strategy": "INTERACTIVE",
            "elk.layered.cycleBreaking.strategy": "DEPTH_FIRST"
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

        Ports: Start nodes need a SOUTH port. Finish nodes need a NORTH port (and EAST/WEST if a bypass line enters them).

2. Process/Action Nodes (Rectangles):

        "myCustomShape": "square"

        "width": 40, "height": 40

        Ports: either NORTH, EAST or WEST (for incoming), SOUTH (for outgoing).

3. Input/Output Nodes (Trapezoid):

        "myCustomShape": "trapezoid"

        "width": 50, "height": 50

        Ports: either NORTH, EAST or WEST (for incoming), SOUTH (for outgoing).


4. Decision Nodes (Diamonds):

        "myCustomShape": "diamond"

        "width": 60, "height": 60

        Crucial Rule: Nodes with side ports MUST include "layoutOptions": { "elk.portConstraints": "FIXED_SIDE" } inside the node definition.

        Ports: NORTH (incoming), SOUTH (the "Yes"/Main flow), and either EAST or WEST (for the "No"/Bypass flow).
      
      
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

    Bypass loops (like "No" branches) MUST exit an EAST or WEST port and enter an EAST or WEST port to prevent overlapping the central spine.

    If a line has text (like "Yes" or "No"), add it to the edge: "labels": [{"text": "Yes"}].
    
---

Output ONLY the raw, valid JSON. Do not include markdown formatting, explanations, or conversational filler.
