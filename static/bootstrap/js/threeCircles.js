function initialize()
{
    // create svg object named svgOb within the div with id circleDiv
    var svgOb = d3.select("#circleDiv").append("svg:svg")
        .attr("width",200)
        .attr("height",200);

    // make some data. we could load a .csv instead
    mydata = [];
    xs = [40, 50, 130];
    ys = [150, 100, 50];
    rad = [20, 10, 5];
    color = ["#ff82ec", "#ffc982", "#82ffa7"];

    // "reshape" the data so the data points for each cell are within one array
    // in the larger array
    // i.e. we want an array whose elements are four-element arrays:
    // an x coord, a y coord, etc.
    for (i=0; i<xs.length; i++)
    {
        mydata.push([xs[i], ys[i], rad[i], color[i]]);
    }

    // create one circle for each data point, mapping the
    // correpsonding datapoints to the respective properties
    svgOb.selectAll(".circle")
        .data(mydata)
        .enter().append("svg:circle")
        .attr("cx", function(d,i) {return d[0]})
        .attr("cy", function(d,i) {return d[1]})
        .attr("r", function(d,i) {return d[2]})
        .style("fill", function(d,i) {return d[3]})
        .style("stroke-width", 1)
        .style("stroke","#000")

    // notes on this .circle thing:
    // selectAll(".circle") will return a "selector" of all elements with the
    // class circle, if they exist. if none exist yet (as in this case), this
    // signals our intent to D3 to create them.
    
    // but how many to create? that's what .data(mydata) is for:
    // it will make one for each array in mydata.
    // what are the circle properties? the center x coord is the 0th
    // (first) item in each subarray in my data, the centr y coord the
    // 1st (second) item, and so forth.
    
    // note for setting properties, we call .attr but for style we call
    // .style. you just have to get used to that and learn which is which
    // style("fill") is the fill color, style("stroke-width") is the width
    // of the circle outline.
    
    // for a complete list of all properties and all types of objects you can
    // make, look at the svg documentation. here it is for circle:
    // http://www.w3.org/TR/SVG/shapes.html#CircleElement
    
    // that url uses a more html-like notation, but it translates directly
    // to this d3/javascript notation.

}