angular.module('flist', []).controller('listCtrl', function($scope, $http, $filter, $log) {
    $http.get("/allFramesData")
    .then(function(response) {
	    
       $scope.frames = response.data;
       for (var i=0; i < response.data.length; ++i ) {
	   $scope.frames[i].createdStr = $filter('date')(response.data[i].created['$date'], "dd-MM-yyyy HH:MM:ss");
	   $scope.frames[i].coordStr = "(" + response.data[i].coord.coordinates[0] + "," + response.data[i].coord.coordinates[1] + ")";
	   $scope.frames[i].binningStr = response.data[i].binningX + "x" + response.data[i].binningY; 		  
       }
        
   }
	)
});



    dashboardApp.controller('calendarCtrl', [ '$scope', function($scope){
	$scope.isExpanded = false;
	$scope.fdata = [];
	$scope.indexId = function(index) {
	    return index;
	}

    }])
    .directive("calendarChart", [ '$filter', function($filter) {
	
    var directiveObj = {
	restrict: 'E',
	replace : false,
	scope : {byear: '=beginYear', eyear: '=endYear', fdata: "="},
	link : function (scope, element, attrs) {

	    var width = $("#calenderView").parent().width() - 30;
	    yearHeight = width / 7,
	    height = yearHeight ,
	    cellSize = yearHeight / 8; // cell size
	    
	    var formatPercent = d3.format(".1%");

	    var color = d3.scaleQuantize()
		.domain([-0.05, 0.05])
		.range(["#a50026", "#d73027", "#f46d43", "#fdae61", "#fee08b", "#ffffbf", "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850", "#006837"]);
	
	    
	    var svgS = d3.select(element[0])
		.selectAll("svg")
		.data(d3.range(scope.byear, scope.eyear))
		.enter().append("svg")
		.attr("width", width)
		.attr("height", height);
	    
	    var svg = svgS
		.append("g")
		.attr("class", "RdYlGn")
		.attr("transform", "translate(" + ((width - cellSize * 53) / 2) + "," + (height - cellSize * 7 - 1) + ")");

	    svg.append("text")
		.attr("transform", "translate(-6," + cellSize * 3.5 + ")rotate(-90)")
		.attr("font-family", "sans-serif")
		.attr("font-size", 10)
		.attr("text-anchor", "middle")
		.text(function(d) { return d; });

	    var rect = svg
		.attr("fill", "none")
		.attr("stroke", "#ccc")
		.selectAll("rect")
		.data(function(d) { return d3.timeDays(new Date(d, 0, 1), new Date(d + 1, 0, 1)); })
		.enter().append("rect")
	        .attr("class", "day")
		.attr("width", cellSize)
		.attr("height", cellSize)
		.attr("x", function(d) { return d3.timeWeek.count(d3.timeYear(d), d) * cellSize; })
		.attr("y", function(d) { return d.getDay() * cellSize; })
		.datum(d3.timeFormat("%Y-%m-%d"))
		.on("click",clickedDay);

	    svg.append("g")
		.attr("fill", "none")
		.attr("stroke", "#000")
		.selectAll("path")
		.data(function(d) { return d3.timeMonths(new Date(d, 0, 1), new Date(d + 1, 0, 1)); })
		.enter().append("path")
	        .attr("class", "month")
		.attr("d", pathMonth);

	    d3.json("/api/v1.0/get_dates", function(error, jdata) {
		if (error) throw error;

		var data = d3.nest()
		    .key(function(d) { return d.date; })
		    .rollup(function(d) { return  d[0].framesOfDay / d[0].framesOfYear; })
		    .object(jdata);

		rect.filter(function(d) { return d in data; })
		    .attr("fill", function(d) { return color(data[d]); })
		    .append("title")
		    .text(function(d) { return d + ": " + formatPercent(data[d]); });
	    });

	    function clickedDay(d){
		d3.json("/allFramesData/"+d, function(error,jdata){
		    if (error) throw error;
		    scope.$parent.fdata = jdata;
		    scope.$parent.$apply();
		});
	    }
	    
	    function pathMonth(t0) {
		var t1 = new Date(t0.getFullYear(), t0.getMonth() + 1, 0),
		    d0 = t0.getDay(), w0 = d3.timeWeek.count(d3.timeYear(t0), t0),
		    d1 = t1.getDay(), w1 = d3.timeWeek.count(d3.timeYear(t1), t1);
		return "M" + (w0 + 1) * cellSize + "," + d0 * cellSize
		    + "H" + w0 * cellSize + "V" + 7 * cellSize
		    + "H" + w1 * cellSize + "V" + (d1 + 1) * cellSize
		    + "H" + (w1 + 1) * cellSize + "V" + 0
		    + "H" + (w0 + 1) * cellSize + "Z";
	    }

	    function resize() {
		var width = $("#calenderView").parent().width() - 30;
		yearHeight = width / 7,
		height = yearHeight ,
		cellSize = yearHeight / 8; // cell size

		svgS.attr("width", width)
		    .attr("height", height);

		svgS.selectAll(".RdYlGn")
		    .attr("transform", "translate(" + ((width - cellSize * 53) / 2) + "," + (height - cellSize * 7 - 1) + ")");
        
		svgS.selectAll(".month").attr("d", pathMonth);
      
		svgS.selectAll(".day")
		    .attr("width", cellSize)
		    .attr("height", cellSize)
		    .data(function(d) { return d3.timeDays(new Date(d, 0, 1), new Date(d + 1, 0, 1)); })
		    .attr("x", function(d) {
			return d3.timeWeek.count(d3.timeYear(d), d) * cellSize;
		    })
		    .attr("y", function(d) {
			return d.getDay() * cellSize;
			});
		
	    };
	    d3.select(window).on('resize', resize);
	}
    }
    return directiveObj;
    } ] );


