function drawMap(region, featureName, scale, center) {
  var width = $(window).width(), height = $(window).height(), centerObj = null;
  if (!center) {
    centerObj = d3.geo.centroid(topojson.feature(region, region.objects[featureName]));
  }
  else {
    centerObj = [center.lon, center.lat];
  }
  d3.selectAll('svg').remove();
  var svg = d3.selectAll('#map').append('svg')
    .attr('width', width)
    .attr('height', height);
  var projection = d3.geo.mercator()
    .scale(scale)
    .translate([width / 2, height / 2])
    .center(centerObj);
  var path = d3.geo.path()
    .projection(projection);
  svg.append("path")
    .datum(topojson.feature(region, region.objects[featureName]))
    .attr("d", path)
    .attr("class", "map-boundary");
  /*
  d3.json(streets_topojson, function(error, streets) {
    console.log(streets);
    svg.selectAll("path.streets").remove();
    svg.append("path")
      .datum(streets)
        .attr("d", path)
        .attr("class", "streets");
  });
  */
  return {path: path, svg: svg, projection: projection, scale: scale};
}

function getCardinalDirection(heading) {
  //given "0-360" returns the nearest cardinal direction "N/NE/E/SE/S/SW/W/NW/N" 
  var directions = 8,
      degree = 360 / directions,
      angle = parseInt(heading) + degree/2;
  
  if (angle >= 0 * degree && angle < 1 * degree)
      return "North";
  if (angle >= 1 * degree && angle < 2 * degree)
      return "North East";
  if (angle >= 2 * degree && angle < 3 * degree)
      return "East";
  if (angle >= 3 * degree && angle < 4 * degree)
      return "South East";
  if (angle >= 4 * degree && angle < 5 * degree)
      return "South";
  if (angle >= 5 * degree && angle < 6 * degree)
      return "South West";
  if (angle >= 6 * degree && angle < 7 * degree)
      return "West";
  if (angle >= 7 * degree && angle < 8 * degree)
      return "North West";
  //Should never happen: 
  return "North";
}

function getDirectionEndpoint(init_lat, init_lon, init_heading, scale) {
  var radius = scale * 0.001 * (26/3959), // Take a fraction of the length of Chicago for a reference
      heading = parseInt(init_heading) * Math.PI / 180,  // Convert everything to radians
      lat = parseFloat(init_lat) * Math.PI / 180,
      lon = parseFloat(init_lon) * Math.PI / 180,
      // Given bearing, initial location and distance, compute new endpoint 
      new_lat = Math.asin(Math.sin(lat) * Math.cos(radius) + Math.cos(lat) * Math.sin(radius) * Math.cos(heading)),
      new_lon = lon + Math.atan2(Math.sin(heading) * Math.sin(radius) * Math.cos(lat), Math.cos(radius) - Math.sin(lat) * Math.sin(new_lat));
  // Have to convert back to degrees
  return [new_lon * 180 / Math.PI, new_lat * 180 / Math.PI];
}

function updateDropdownRoutes(positions) {
  var routes = _.uniq(_.pluck(positions, 'route'), true),
      template = _.template($('#select_route_tmpl').html());
  _.each(routes, function(route) {
    $('#select_route').append(template({ route: route }));
  })
}

function updatePositions(map, user, updateDropdown) {
  d3.json(positions_json[current_positions], function(error, positions) {
    if (updateDropdown) {
      updateDropdownRoutes(positions);
      $('#select_route').change(function() {
        selected_route = $('#select_route').val();
        $('#select_trains').removeClass('active');
        $('#select_buses').removeClass('active');
        $('#select_all').removeClass('active');
        updatePositions(map, user);
      });
    }
    var svg = map.svg,
        projection = map.projection;
    var filtered = _.filter(positions, function(position) {
      if (selected_route == '')
        return true;
      else if (selected_route == position.route)
        return true;
      return false;
    });
    if (user && user.lat && zoomed) {
      updateClosestPositions(positions, user);
      svg.selectAll(".user_position").remove();
      svg.selectAll("circle.user_position")
        .data([user]).enter()
          .append("circle")
          .attr("cx", function(d) { return projection([d.lon, d.lat])[0]; })
          .attr("cy", function(d) { return projection([d.lon, d.lat])[1]; })
          .attr("r", "10px")
          .attr("stroke", "#aaa")
          .attr("fill", "rgba(255, 255, 255, 0.9")
          .attr("class", "user_position")
          .append("svg:title")
            .text('You are here');
      svg.selectAll("line.user_position")
        .data([
          getDirectionEndpoint(user.lat, user.lon, 0, map.scale/180000),
          getDirectionEndpoint(user.lat, user.lon, 45, map.scale/180000),
          getDirectionEndpoint(user.lat, user.lon, 90, map.scale/180000),
          getDirectionEndpoint(user.lat, user.lon, 135, map.scale/180000),
          getDirectionEndpoint(user.lat, user.lon, 180, map.scale/180000),
          getDirectionEndpoint(user.lat, user.lon, 225, map.scale/180000),
          getDirectionEndpoint(user.lat, user.lon, 270, map.scale/180000),
          getDirectionEndpoint(user.lat, user.lon, 315, map.scale/180000),
          ]).enter()
          .append("line")
          .attr("x1", function(d) { return projection([d[0], d[1]])[0]; })
          .attr("y1", function(d) { return projection([d[0], d[1]])[1]; })
          .attr("x2", function() { return projection([user.lon, user.lat])[0]; })
          .attr("y2", function() { return projection([user.lon, user.lat])[1]; })
          .attr("stroke", "#777")
          .attr("class", "user_position")
          .append("svg:title")
            .text('You are here');
      map.projection = map.projection.scale(680000);
    }
    svg.selectAll("circle.vehicle").remove();
    svg.selectAll("circle.vehicle")
      .data(filtered).enter()
        .append('circle')
        .attr("cx", function(d) { return projection([d.lon, d.lat])[0]; })
        .attr("cy", function(d) { return projection([d.lon, d.lat])[1]; })
        .attr("r", function() { return (map.scale/30000) + "px"; })
        .attr("fill", function(d) {
          if (d.type == 'bus')
            return 'rgba(255, 255, 255, 0.1)';
          else
            return d.color;
        })
        .attr("stroke", function(d) { return d.color })
        .attr("class", "vehicle")
        .on("mouseover", function(d) {
          var tmpl = _.template($('#vehicle_tmpl').html());
          tooltip.html(tmpl({vehicle: d}));
          return tooltip.style("visibility", "visible");
        })
        .on("mousemove", function() { return tooltip.style("top",
          (d3.event.pageY - 10) + "px").style("left", (d3.event.pageX + 10) + "px"); })
        .on("mouseout", function() { return tooltip.style("visibility", "hidden"); });

      svg.selectAll("line.direction").remove();
      svg.selectAll("line.direction")
        .data(filtered).enter()
          .append("line")
          .attr("x1", function(d) { return projection([d.lon, d.lat])[0]; })
          .attr("y1", function(d) { return projection([d.lon, d.lat])[1]; })
          .attr("x2", function(d) { return projection(getDirectionEndpoint(d.lat, d.lon, d.heading, map.scale/60000))[0]; })
          .attr("y2", function(d) { return projection(getDirectionEndpoint(d.lat, d.lon, d.heading, map.scale/60000))[1]; })
          .attr("stroke", function(d) { return d.color })
          .attr("opacity", "0.8")
          .attr("class", "direction");
  });
}

function updateClosestPositions(positions, user) {
  var filtered = _.filter(positions, function(position) {
    if (selected_route == '')
      return true;
    else if (selected_route == position.route)
      return true;
    return false;
  });
  filtered.sort(function(a, b) {
    return getDistance(user.lat, user.lon, a.lat, a.lon) - getDistance(user.lat, user.lon, b.lat, b.lon);
  });
  var footer = '<p>Nearest vehicles to you:<br><hr>',
      footer_tmpl = _.template($('#info_footer_tmpl').html());
  for (var i = 0; i < 5; i++) {
    footer += footer_tmpl({position: filtered[i], user: user});
  }
  footer += '</p>';
  $('#info_pane').html(footer);
  $('#info_pane').show();

}

function getDistance(lat1, lon1, lat2, lon2) {
  var radlat1 = Math.PI * lat1 / 180,
      radlat2 = Math.PI * lat2 / 180,
      radlon1 = Math.PI * lon1 / 180,
      radlon2 = Math.PI * lon2 / 180,
      theta = lon1-lon2,
      radtheta = Math.PI * theta / 180,
      dist = Math.sin(radlat1) * Math.sin(radlat2) + Math.cos(radlat1) * Math.cos(radlat2) * Math.cos(radtheta),
      dist = Math.acos(dist),
      dist = dist * 180 / Math.PI,
      dist = dist * 60 * 1.1515;
  return dist
}

$(document).ready(function() {
  var user = { lat: null, lon: null };
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(position) {
      user.lat = position.coords.latitude;
      user.lon = position.coords.longitude;
    });
  }
  tooltip = d3.select("body")
    .append("div")
    .style("position", "absolute")
    .style("z-index", "10")
    .style("visibility", "hidden")
    .attr("class", "map_tooltip");
  d3.json(chicago_topojson, function (error, chicago) {
    map = drawMap(chicago, 'chicago', 60000, null);
    updatePositions(map, user, true);
    setInterval(function() {
      updatePositions(map, user);
    }, 5000);

    $('#find_me').click(function() {
      if (user.lat && user.lon) {
        if (!zoomed) {
          map = drawMap(chicago, 'chicago', 680000, user);
          zoomed = true;
          updatePositions(map, user);
          $('#find_me').text('Zoom out');
        } else {
          map = drawMap(chicago, 'chicago', 60000, null);
          zoomed = false;
          updatePositions(map, user);
          $('#find_me').text('Find me');
          $('#info_pane').hide();
        }
      }
    });
    $('#select_trains').click(function() {
      current_positions = 'trains';
      selected_route = '';
      updatePositions(map, user);
      $('#select_trains').addClass('active');
      $('#select_buses').removeClass('active');
      $('#select_all').removeClass('active');
    });
    $('#select_buses').click(function() {
      current_positions = 'buses';
      selected_route = '';
      updatePositions(map, user);
      $('#select_trains').removeClass('active');
      $('#select_buses').addClass('active');
      $('#select_all').removeClass('active');
    });
    $('#select_all').click(function() {
      current_positions = 'all';
      selected_route = '';
      updatePositions(map, user);
      $('#select_trains').removeClass('active');
      $('#select_buses').removeClass('active');
      $('#select_all').addClass('active');
    });
  });
});