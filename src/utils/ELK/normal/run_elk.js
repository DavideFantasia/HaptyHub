const ELK = require('elkjs');
const fs = require('fs');

const elk = new ELK();

// 1. Read your blueprint
const inputGraph = JSON.parse(fs.readFileSync('input_blueprint.json', 'utf8'));

// 2. Run the ELK engine to calculate the layout
elk.layout(inputGraph)
   .then(outputGraph => {
       // 3. Save the new file containing all the exact X/Y measurements
       fs.writeFileSync('output_coordinates.json', JSON.stringify(outputGraph, null, 2));
       console.log("Success! Your exact OpenSCAD coordinates are ready.");
   })
   .catch(console.error);
