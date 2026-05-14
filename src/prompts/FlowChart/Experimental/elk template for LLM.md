Your task is to translate this visual flowchart into a strict ELK (Eclipse Layout Kernel) JSON format for a 3D-printing pipeline.

---

# Global Layout Rules:
Start the JSON with the following exact root configuration to enforce 90-degree Manhattan routing and fixed ports:

       {
        "id": "root",
        "layoutOptions": {
        "elk.algorithm": "layered",
        "elk.direction": "DOWN",
        "elk.alignment": "CENTER",
        "elk.edgeRouting": "ORTHOGONAL",
        "elk.padding": "[top=150,left=300,bottom=150,right=300]",
        "elk.spacing.nodeNode": "100",
        "elk.spacing.edgeNode": "100",
        "elk.spacing.edgeEdge": "50",
        "elk.layered.crossingMinimization.numIterations": "100",
        "elk.layered.spacing.nodeNodeBetweenLayers": "100",
        "elk.layered.spacing.edgeNodeBetweenLayers": "50",
        "elk.layered.compaction.postCompaction.strategy": "NONE",
        "elk.layered.layering.strategy": "NETWORK_SIMPLEX",
        "elk.layered.cycleBreaking.strategy": "DEPTH_FIRST",
        "elk.portConstraints": "FIXED_SIDE",
        "elk.layered.spacing.dummyNodeNodeBetweenLayers": "100",
        "elk.layered.unnecessaryBendpoints": "true",
        "elk.edgeLabels.placement": "UNDEFINED"
    },
        "children": [],
        "edges": []
        }

---

# Agent goal
Your goal is a PLANAR, non-crossing logical graph.

If you detect a crossing line in the image, you MUST conceptually untangle it before generating the JSON:
1. Identify the origin port of the branch (e.g., the WEST port of a Decision node).
2. Conceptually relocate the target node to the SAME SIDE as the origin.
3. Route the edges accordingly: the edge must stay on that side, enter the target's NORTH port, and if that secondary branch merges back into the main center flow, it MUST enter the center node's corresponding port (e.g., a WEST-originating branch must enter the final node's WEST port).

Rule of Thumb: Never force an edge to cross the center spine just because the visual sketch did. Prioritize topological cleanliness and port consistency over the visual literalism of the user's sketch.

---

# Node Definition Rules (The children array):
For every shape in the flowchart, create a node object. You MUST include a custom "myCustomShape" attribute and assign sizes and ports exactly as follows:

Crucial Rule for Merging (SPATIAL CONSISTENCY): ANY node that receives multiple incoming edges MUST use different cardinal directions to avoid overlapping. 
HOWEVER, you MUST explicitly respect the topological side of the branch:
    - If a secondary branch originated from an EAST port of a Decision node (meaning it lives on the right side of the flowchart), any downstream connection that merges back into the main center flow MUST enter the target node's EAST port.
    - If a branch originated from a WEST port, it MUST merge back via the WEST  port.
    - NEVER cross the center spine (e.g., DO NOT exit an EAST port upstream and enter a WEST port downstream).

1. Start/Finish Nodes (Circles/Ovals):

        "myCustomShape": "circle"

        "width": 40, "height": 40
        
                Crucial Rule: Nodes with side ports MUST include "layoutOptions": { "elk.portConstraints": "FIXED_SIDE" } inside the node definition.

        Ports: Start nodes need a SOUTH port. Finish nodes need a NORTH port. (if two or more ports arrive at the finish node DO NOT merge them in the north port).If two or more nodes exit the START node, assigne the SOUTH port to one and either EAST or WEST to the other.

2. Process/Action Nodes (Rectangles):

        "myCustomShape": "square"

        "width": 40, "height": 40
        
                Crucial Rule: Nodes with side ports MUST include "layoutOptions": { "elk.portConstraints": "FIXED_SIDE" } inside the node definition.

        Ports: either NORTH, EAST or WEST (for incoming), SOUTH (for outgoing).

3. Input/Output Nodes (Trapezoid):

        "myCustomShape": "trapezoid"

        "width": 40, "height": 40
        
                Crucial Rule: Nodes with side ports MUST include "layoutOptions": { "elk.portConstraints": "FIXED_SIDE" } inside the node definition.

        Ports: either NORTH, EAST or WEST (for incoming), SOUTH (for outgoing).


4. Decision Nodes (Diamonds):

        "myCustomShape": "diamond"

        "width": 40, "height": 40

        Crucial Rule: Nodes with side ports MUST include "layoutOptions": { "elk.portConstraints": "FIXED_SIDE" } inside the node definition.

        Ports: NORTH (incoming), SOUTH (the "Yes"/Main flow), and either EAST or WEST (for the "No"/Bypass flow).
        
5. Ranking and Layering:
To ensure nodes are positioned in the correct vertical rank relative to the flowchart's flow:

    Assign a "layoutOptions": { "elk.layered.layering.layer": "X" } to each node.

    The top-most node (Start) should be layer 0.

    Each subsequent step down the flowchart should increment the layer number (e.g., 1, 2, 3).

    Nodes that appear side-by-side (like the RIGHT or LEFT branch of a decision node) should typically share the same layer number as the node they are logically aligned with.
    
   Decision Branches: Edges that exit the EAST or WEST ports of a Diamond MUST always target the NORTH port of the destination node.
        
    
      
      
## Node Labels:
For every node, you MUST include a labels array containing the text found inside the shape in the flowchart.

Syntax: "labels": [{ "text": "Node Text Here" }]

Place this inside the node object alongside id and myCustomShape.

if the node contains no text, just leave the field empty
        
        
## Port Syntax:
Ports must be defined strictly like this:
        {"id": "nodeName_out_south", "layoutOptions": { "elk.port.side": "SOUTH" }}

---

#Edge Definition Rules (The edges array):
Trace every line in the flowchart.

    Define "source" and "target" node IDs.

    You MUST explicitly map the "sourcePort" and "targetPort".

    Vertical center flow should go SOUTH to NORTH.

If a node is placed on the exact same layer as the node it originates from, the incoming edge MUST enter the WEST port (if coming from the left) or the EAST port (if coming from the right), NEVER the NORTH port.

    If a line has text (like "Yes" or "No"), add it to the edge: "labels": [{"text": "Yes"}].
    
    STRICT PORT UNIQUENEES: A single port (ID) cannot function as both a sourcePort and a targetPort within the same JSON. (for example there cannot be in the same node a _in_north and _out_north).
    If in the provided image, the same  port function as both in and out, assign those two to 2 different ports.

    Collision Avoidance: If an edge exits a node's EAST port, no incoming edge can target that same node's EAST port as an entry!
    
    
---

#Port Conflict Logic:

Before generating, verify: Is any port ID used in both the "source" of one edge and the "target" of another? If yes, move the incoming edge to an unused cardinal side (WEST or NORTH).

If the same port is both the target of an edge and the starting point of another edge, move one of the two to another free port.
     
also verify that each edge correctly connects to the right node.
    
---

#Final Execution Instructions:

    Analyze the Image: Identify all shapes, text labels, and connection directions.

    Layer Assignment: Map out the vertical layers (0, 1, 2...). If a decision "No" branch points to a node logically side-by-side, assign it the same layer as the decision node.

    Port Verification: Before outputting, perform a "dry run" of the edge list. If an edge ID (e.g., NodeA_out_east) is used as a sourcePort, ensure that same ID is never used as a targetPort.

    Collision Check: If a node has an outgoing edge on the EAST side, move any incoming side-edges to the WEST side.
    
    If possible rearrange ports in order to avoid crossings.

    Strict Output: Output ONLY the valid JSON object. No prose. No markdown code blocks unless requested.

Output ONLY the raw, valid JSON. Do not include markdown formatting, explanations, or conversational filler.

---

