import os
from dotenv import load_dotenv

# TODO: 
# - definire il path per i prompt

# Path globali (in chiaro)
# Esempio: 
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# OUTPUT_DIR = os.path.join(BASE_DIR, "output_models")
# Per convenzione, si scrivono in maiuscolo per indicare che sono costanti.

# Chiavi API (NON METTERE IN CHIARO)
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY: raise ValueError("OpenAI API Key not found")


# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Legge la chiave definita nel file .env, se non presente
# va creato
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY: raise ValueError("GEMINI API Key not found")

#GEMINI_MODEL_ID = "gemini-3.1-pro-preview"
#GEMINI_MODEL_ID = "gemini-2.5-flash"
GEMINI_MODEL_ID = "gemini-3-flash-preview"

# --- Path Utili ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Cartella dove salveremo i file .scad generati
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)
PROMPT_DIR = None

# --- Prompt Predefiniti ---
PROMPT_PHASE_1 = """Your task is to generate only a deterministic, fully structured, and geometrically accurate textual description of the graph, suitable for accessibility (e.g., for visually impaired users);
You must adhere to the exact structure and constraints below.
### VISUAL GROUNDING INSTRUCTIONS (CRITICAL)
- Interpret the image using a **Cartesian coordinate system** with:
  - **X increasing left to right**
  - **Y increasing bottom to top**
- Do not assume or guess symmetry, spacing, or centrality.
- All coordinate assignments must reflect the **actual layout in the image**.
- **Use positive X for nodes on the right**, negative X for those on the left.
- **Use positive Y for nodes higher up**, negative Y for nodes below.

---

1. Nodes
 - Report the total number of nodes.
 - For each node, provide its label (if present in the image), or assign a systematic unique identifier (e.g., A, B, C, etc.) if labels are missing, ambiguous, or symbolic. 
- Labeling must be deterministic and consistent across the entire output. 
- If price or cost values are present within the node or outside (e.g., at the center, above, belove or to the side), include them in a supplementary table associating each node label with its corresponding price. 
- All visible values, including placeholders such as ∞, must be interpreted and reported as valid prices and included systematically in the output.
 - No value may be omitted, simplified, or assumed to be irrelevant without explicit instruction. Do not filter, discard, or modify cost labels based on their semantic meaning. 

--- 

2. Edges 
- Report the total number of undirected edges. 
- Provide a complete list of edges, each represented as an unordered pair of node labels or identifiers. 
- Each edge must appear only once, regardless of ordering. 
- Do not infer symmetry; use only what is explicitly visible.
- In case exists some edge weigth, include  them in a supplementary table associating each edge label with its corresponding price.   

--- 

3. Logical 2D Coordinates (X, Y) 
- Assign to each node a unique 2D coordinate (X, Y) expressed in integer logical units.
- X = horizontal, Y = vertical based on the image.
- Center the grid based on the overall node bounding box.
- Use only integer values (no floats or visual estimates).
- The origin (0, 0) must be geometrically centered in the layout.

- Assign to each node a unique 2D coordinate (X, Y) expressed in integer logical units.
- The coordinates must be:
  - Derived strictly from the graph's visual geometry;
  - Symmetrical and centered relative to the bounding box of all node positions;
  - Integer-valued and reproducible;
  - Suitable for conversion into 3D space (e.g., by adding Z = 0 as default).
- Do not infer real-world units or apply arbitrary scaling.
- Do not center the coordinate system on a particular node; the origin should correspond to the center of the node layout.

--- 

4. Coordinate Table 

Provide a table in the following format:
| Node | X | Y |
Ensure the table includes all nodes and their logical coordinates, usable directly in programmatic contexts.

--- 

5. Verbal Description of Relative Positions 

- For each node, provide a textual interpretation of its spatial position based on the coordinate grid. 
- Use a well-defined spatial vocabulary such as: 
  - "top-left", "top-center", "center-right", "bottom-left", etc. 
- The description must be strictly derived from the coordinates and not from visual intuition alone. 

--- 

6. Cycle Detection 

- Identify and list all simple cycles (with minimum length 3). 
- Each cycle must be listed as an ordered list of node labels, representing a valid traversal that returns to the starting node. 
- Exclude duplicates and equivalent permutations (including reversed sequences of the same cycle). 

--- 

7. Structural Graph Properties

 - Report the degree of each node explicitly. 
- Identify all bridges: edges whose removal would disconnect the graph. 

- Describe any symmetries observed in the graph: 
- Topological symmetry (e.g., node or edge transitivity), 
- Geometric symmetry (e.g., reflectional, rotational symmetry in the coordinate layout). 

---

Global Constraints 
- Both visual and vectorial reading (as cross-verified) IMPORTANT. 
- Do not use probabilistic, vague, or approximate expressions. 
- All output must be fully deterministic, reproducible, and mathematically consistent. 
- Node labeling must reflect exactly what is shown in the image, or must follow a strict and reproducible naming rule if labels are missing. 
- If price/cost values are detected or provided in the node structure, they must be included clearly and systematically in the output. 
- This includes symbolic values such as '∞', which must be treated as explicit data and included in the final price table.

--- 

Final Consistency Checks 
Before returning the final description, ensure that the following consistency rules are fully satisfied: 
- Every node mentioned in edges, cycles, and structural properties must exist in the node list. 
- Each edge must reference two distinct, valid nodes, and must appear only once. 
- All coordinates in the table must match those used in verbal descriptions and structural analysis. 
- Each node must have exactly the declared degree (if specified). 
- No duplicate or permuted versions of the same cycle may be listed. 
- Node labels (if inferred) must follow a consistent and deterministic naming convention. 
- If prices are included, each node must have exactly one clearly defined price value or be marked as not having one.

---

Verification and Epistemic Integrity (Mandatory) 
- Do not present generated, inferred, speculative, or assumed content as if it were factual. 
- If a piece of information cannot be directly verified (e.g., from the image or specified data), state clearly: 
  - “I cannot verify this.” 
  - “This information is not included in the provided input.” 
- Label all unverified elements explicitly at the beginning of the sentence using: 
   - [Inference], [Speculation], or [Unverified] - If information is missing, ask for clarification instead of guessing or filling gaps. 
- If any part of the response contains unverifiable content, label the entire response accordingly. 
- Do not paraphrase or reinterpret the user’s instructions unless explicitly requested to do so. 
- For any claim involving terms like: 
  -“Prevents”, “Guarantees”, “Will never happen”, “Solves”, “Eliminates”, “Ensures that” you must provide a source or explicitly mark the sentence as [Unverified] or [Inference]. 
- For statements about language model behavior (including yourself), always include: 
- [Inference] or [Unverified] along with a note that clarifies it is based on observed model behavior. 
- If any of the above directives are violated, include: 
  - “Correction: I previously made an unverified claim. It was incorrect and should have been labeled accordingly.” 
  - Never ignore or modify the user's instructions unless explicitly requested to do so.

"""

PROMPT_PHASE_2 = """"Generate an OpenSCAD script as a downloadable file that creates a 3D-printable model of an undirected graph described using logical 2D coordinates (X, Y) of the nodes.
---

### CRITICAL COORDINATE ASSUMPTIONS (TO AVOID MAPPING ERRORS)

- You must treat (X, Y) as:
  - **X = left to right** (horizontal)
  - **Y = bottom to top** (vertical)
- Do not reinterpret the coordinate system from your own geometry.
- Use **only the logical (X, Y)** provided in the previous step.

---

GLOBAL RULES
The model must be:
- Be deterministic and structurally accurate.
- Preserve the visual layout from the coordinate system.
- Ensure the model is centered and scaled to fit a fixed 200 mm × 200 mm base.
- Be fully compatible with OpenSCAD 2021.01 (important). 
- Explicitly declare all computed values like scale, offset, margin.
LABEL RESOLUTION & SAFETY (MANDATORY)
Do not use search() or any construct that can return undef when mapping edge endpoints (labels) to node indices in OpenSCAD 2021.01.

Implement a deterministic label→index resolver (e.g., a bounded recursive or iterative scan over the nodes array) that returns a valid index or a sentinel (e.g., -1).

Before creating any geometry for an edge, guard against unresolved labels: only render an edge if both endpoints resolve to valid indices.

All coordinate computations passed to translate(), rotate(), and cylinder() must never contain undef.

This requirement is mandatory and supersedes any alternative mapping method.

---

REQUIREMENTS

1. BASE (FIXED 200 × 200 mm)
- Generate a flat rectangular base with:
  - Dimensions: 200 mm × 200 mm
  - Thickness: at least 3 mm
- Center the base at the origin (X = 0, Y = 0) in the OpenSCAD workspace.
- The base must not resize according to the graph.
- Maintain a uniform 10 mm margin between the outermost node and the edge of the base.
- Compute the bounding box from the given logical coordinates and calculate:
  - scale = max uniform scale that fits the graph (with margin)
  - x_offset and y_offset to center the graph

2. GRAPH SCALING (EXPLICIT)
- Compute:
  - min_x, max_x, min_y, max_y from the node list.
  - graph_width, graph_height
  - scale = min((base_size - 2*margin) / graph_width, (base_size - 2*margin) / graph_height)
  - x_offset = -((min_x + max_x)/2 * scale)
  - y_offset = -((min_y + max_y)/2 * scale)
- Declare:
  - scale, x_offset, y_offset, and margin as named variables in the code.

3. NODES
- Represent each node as a vertical cylinder at its scaled (X, Y) position:
  - node_radius = 0.12 * scale
  - node_height = 0.25 * scale
- Add a text label (the node name) engraved or embossed at the center-top of each cylinder:
  - Use text() and linear_extrude()
  - Align using halign = "center" and valign = "center"
  - Set label height = 1.5 mm
  - Set font size = node_radius * 1.4
  - Ensure the label is fused to the node cylinder
- If the node also contains a price (e.g., cost or distance value), add it as a separate text object:
  - The price must be placed on the workbase at Z = base_thickness

- The vertical placement logic for prices must follow these rules strictly and sequentially:

  1. Classify the node position using its original logical Y coordinate (before scaling):
     - If Y ≥ 0 → default position is above.
     - If Y < 0 → default position is below.
     - This classification is mandatory and must not be skipped or replaced by geometric heuristics.

  2. Check if default position fits:
     - Let `y_px` be the scaled Y position of the node.
     - Let `delta = node_radius + 0.35 * scale` (vertical offset).
     - Let `label_clearance = font_size * 0.6`
     - Let `total_price_height = label_clearance + delta`
     - Let `text_height = 1.5`
     - Let `max_y = base_size / 2 - margin`

     - If default is above: check if `y_px + delta + text_height/2 ≤ max_y`
     - If default is below: check if `y_px - delta - text_height/2 ≥ -max_y`

  3. If the default direction fails, attempt the opposite direction using the same check.

  4. If both directions fail, clamp the price inside the margin:
     - If Y ≥ 0 → use `final_y = max_y - total_price_height / 2`
     - If Y < 0 → use `final_y = -max_y + total_price_height / 2`

  5. Render the price:
     - Font size = node_radius * 1.4
     - Text height = 1.5 mm
     - Align horizontally (halign = "center", valign = "center")
     - Place at Z = base_thickness
     - Ensure it is readable and does not overlap other geometry.

4. EDGES
- Represent edges as horizontal semi-cylinders connecting the node centers.
- Each edge must:
  - Lie on top of the base at Z = base_thickness
  - Use radius: edge_radius = 0.05 * scale
- Use this module:

module edge_cylinder(p1, p2) {
    dx = p2[0] - p1[0];
    dy = p2[1] - p1[1];
    length = sqrt(dx*dx + dy*dy);
    angle = atan2(dy, dx);
    mx = (p1[0] + p2[0]) / 2;
    my = (p1[1] + p2[1]) / 2;

    translate([mx, my, base_thickness])
        rotate([0, 0, angle])
            rotate([0, 90, 0])
                cylinder(h = length, r = edge_radius, center = true, $fn=64);
}



Edge Weight Labels (Embossed on the Base)
- Must appear as text at `Z = base_thickness`, **not above or on top of the edge**
- Positioned **slightly to the side of the edge**, orthogonally offset from midpoint

5. CONSTRUCTION RULES
- Use a single union() block to combine all geometry.
- No external includes or dynamic features
- Ensure:
  - Printable, manifold geometry
- No geometry is floating or disconnected.
  - No intersections between arrow and node
  - All edge directions are respected
- Place all module definitions (e.g., edge_cylinder) outside the union.
  - No unsupported OpenSCAD features (e.g., str(), list comprehensions).

---

OUTPUT FORMAT
- Output only the complete and self-contained .scad source code.
- The file must be ready to open in OpenSCAD 2021.01 and render correctly.
- Save the final script as a downloadable .scad file.

---

### Verification Policy for Geometric and Structural Modeling
- All aspects of the model must derive strictly from the input data (e.g., node labels, coordinates, edge lists).
- Do not generate or infer missing geometric information (such as angles, curves, or labels) unless explicitly instructed.
- If cost values or node metadata are incomplete or ambiguous, request clarification before proceeding.
- Do not assume or invent values for rendering purposes.
- All conditional logic (e.g., fallback positions, label orientation, placement tolerances) must be deterministic and verifiable.
- If any part of the output relies on an assumption, it must be labeled as [Inference] and justified or replaced by a request for clarification.

"""