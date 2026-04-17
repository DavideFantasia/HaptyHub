// --- GLOBAL SETTINGS & CONSTANTS ---
$fn = 64;
base_width = 135;
base_height = 217;
base_thickness = 1.5;
rounding_radius = 1; 

block_size = 17;   
outline_thickness = 1;
bb_h = 2; 
edge_radius = 1; 

shape_radius = (block_size / 2) + 1;
radius_diamond = (block_size / 2) * sqrt(2); 
radius_trapezoid = (block_size / 2) + (block_size * 0.15); 

arrow_length = 4;
arrow_width = 3.5;
margin_x = 14.115;
margin_y = 18.325;

// --- DYNAMIC GRID & SPACING ---
min_x = 40.33333333333333; max_x = 145.33333333333331;
min_y = -662.0; max_y = -32.0;

safe_margin_x = margin_x + (block_size / 2);
safe_margin_y = margin_y + (block_size / 2);
grid_spacing = min((base_width - (safe_margin_x * 2)) / max(1, (max_x - min_x)), 
                   (base_height - (safe_margin_y * 2)) / max(1, (max_y - min_y)));
                
x_offset = (base_width / 2) - ((min_x + max_x) / 2 * grid_spacing);
y_offset = (base_height / 2) - ((min_y + max_y) / 2 * grid_spacing);
function scale_p(p) = [p[0] * grid_spacing + x_offset, p[1] * grid_spacing + y_offset];

// --- SOLID PRIMITIVES & HELPER MODULES ---
module draw_shape(type) {
    if (type == "circle") circle(d = block_size, $fn=64);
    else if (type == "trapezoid") offset(r = rounding_radius) polygon([[-block_size/2+(block_size*0.15), block_size/2], [block_size/2+(block_size*0.15), block_size/2], [block_size/2-(block_size*0.15), -block_size/2], [-block_size/2-(block_size*0.15), -block_size/2]]);
    else if (type == "diamond") offset(r = rounding_radius) rotate([0, 0, 45]) square([block_size, block_size], center=true);
    else offset(r = rounding_radius) square([block_size, block_size], center=true);
}

module place_node(x, y, type, mode="wall") {
    p = scale_p([x, y]);
    if (mode == "hole") {
        translate([p[0], p[1], -1]) 
            linear_extrude(base_thickness + 2) 
                offset(delta=-outline_thickness) union() { draw_shape(type); }
    } else {
        // Sunk 0.1mm into the baseplate to prevent "floating" geometry
        translate([p[0], p[1], base_thickness - 0.1]) {
            difference() {
                linear_extrude(bb_h + 0.1) union() { draw_shape(type); }
                translate([0, 0, -0.1]) 
                    linear_extrude(bb_h + 1) 
                        offset(delta=-outline_thickness) union() { draw_shape(type); }
            }
        }
    }
}

// --- EDGE ROUTING MODULES ---
module edge_segment(p1, p2, is_start=false, is_end=false, src="square", tgt="square") {
    p1s = scale_p(p1); p2s = scale_p(p2);
    dx = p2s[0] - p1s[0]; dy = p2s[1] - p1s[1];
    dist = sqrt(dx*dx + dy*dy); angle = atan2(dy, dx);
    sg = is_start ? ((src == "diamond" ? radius_diamond + 2 : shape_radius + 1)) : 0;
    eg = is_end ? ((tgt == "diamond" ? radius_diamond + 2 : shape_radius + 1) + arrow_length) : 0;
    if (dist - sg - eg > 0) translate([p1s[0] + cos(angle)*sg, p1s[1] + sin(angle)*sg, base_thickness]) rotate([0, 90, angle]) cylinder(h = dist - sg - eg, r = edge_radius, $fn=24);
}

module edge_elbow(p) { 
    v = scale_p(p); 
    // Sunk slightly to ensure safe 3D printing
    translate([v[0], v[1], base_thickness - 0.1]) sphere(r = edge_radius, $fn=32); 
}

module edge_arrow(p1, p2, tgt="square") {
    p1s = scale_p(p1); p2s = scale_p(p2);
    angle = atan2(p2s[1] - p1s[1], p2s[0] - p1s[0]);
    gd = (tgt == "diamond") ? radius_diamond + 2 : shape_radius + 1;
    // Sunk 0.1mm into baseplate
    translate([p2s[0] - cos(angle)*gd, p2s[1] - sin(angle)*gd, base_thickness - 0.1]) 
        rotate([0, 0, angle]) 
            linear_extrude(height = edge_radius + 0.1) 
                polygon(points=[[0, 0], [-arrow_length, -arrow_width / 2], [-arrow_length, arrow_width / 2]]);
}

module edge_label(p1, p2, text_val) {
    p1s = scale_p(p1); p2s = scale_p(p2);
    angle = atan2(p2s[1] - p1s[1], p2s[0] - p1s[0]);
    adj_angle = (angle > 90 || angle < -90) ? angle + 180 : angle; 
    // Sunk 0.1mm into baseplate
    translate([(p1s[0] + p2s[0])/2 - sin(angle)*5, (p1s[1] + p2s[1])/2 + cos(angle)*5, base_thickness - 0.1])
        rotate([0, 0, adj_angle]) 
            linear_extrude(height=1.1) 
                text(text_val, size=4, spacing=1.5, valign="center", halign="center");
}

// --- TOP LEVEL RENDERING ---
union() {
    difference() {
        cube([base_width, base_height, base_thickness]);

        place_node(42.0, -32.0, "circle", "hole");
        place_node(42.0, -162.0, "diamond", "hole");
        place_node(40.33333333333333, -457.0, "trapezoid", "hole");
        place_node(47.0, -662.0, "circle", "hole");
    }

    place_node(42.0, -32.0, "circle", "wall");
    place_node(42.0, -162.0, "diamond", "wall");
    place_node(40.33333333333333, -457.0, "trapezoid", "wall");
    place_node(47.0, -662.0, "circle", "wall");
    edge_segment([42.0, -32.0], [42.0, -162.0], true, true, "circle", "diamond");
    edge_arrow([42.0, -32.0], [42.0, -162.0], "diamond");
    edge_segment([42.0, -162.0], [52, -272], true, false, "diamond", "circle");
    edge_segment([52, -272], [145.33333333333331, -272], false, false, "diamond", "circle");
    edge_elbow([52, -272]);
    edge_segment([145.33333333333331, -272], [145.33333333333331, -457], false, false, "diamond", "circle");
    edge_elbow([145.33333333333331, -272]);
    edge_segment([145.33333333333331, -457], [145.33333333333331, -562], false, false, "diamond", "circle");
    edge_elbow([145.33333333333331, -457]);
    edge_segment([145.33333333333331, -562], [53.666666666666664, -562], false, false, "diamond", "circle");
    edge_elbow([145.33333333333331, -562]);
    edge_segment([53.666666666666664, -562], [47.0, -662.0], false, true, "diamond", "circle");
    edge_elbow([53.666666666666664, -562]);
    edge_arrow([53.666666666666664, -562], [47.0, -662.0], "circle");
    edge_label([145.33333333333331, -272], [145.33333333333331, -457], "YES");
    edge_segment([42.0, -162.0], [40.33333333333333, -457.0], true, true, "diamond", "trapezoid");
    edge_arrow([42.0, -162.0], [40.33333333333333, -457.0], "trapezoid");
    edge_label([42.0, -162.0], [40.33333333333333, -457.0], "NO");
    edge_segment([40.33333333333333, -457.0], [47.0, -662.0], true, true, "trapezoid", "circle");
    edge_arrow([40.33333333333333, -457.0], [47.0, -662.0], "circle");
}