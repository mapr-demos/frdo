var frdostorage = window.localStorage;
var FRDO_BACKEND_URL = 'http://localhost:6996';
var FRDO_TEST_HEATMAP = '/api/heatmap/test'
var FRDO_HEATMAPS = '/api/heatmap'
var backendURL = FRDO_BACKEND_URL;
var heatmaps = [];
var currentHeatmapPointer = 0;

$(function(){
  
  initForms();
  
  getHeatmapList();
    
  $('#about').click(function(){
    $('#about-dialog').modal('toggle');
    return false;
  });

  $('#refresh-heatmap').click(function(){
    currentHeatmapPointer += 1;
    if(currentHeatmapPointer == heatmaps.length){
      currentHeatmapPointer = 0;
    }
    console.log('Current heatmap: ' + heatmaps[currentHeatmapPointer]);
    $("#current-heatmap").html('current: ' + heatmaps[currentHeatmapPointer]);
    renderHeatmap(heatmaps[currentHeatmapPointer]);
    return false;
  });
  
  $('#query-execute').click(function(){
    executeQuery();
    return false;
  });

});

// init forms
function initForms(){
  
  $('#about-dialog').modal({
    backdrop: true,
    keyboard: true,
    show: false
  });
  renderHeatmap();
}

// init the heatmap with Google maps and render some test data
function renderHeatmap(hmFile) {
  var centerLatlng = new google.maps.LatLng(40, -2);
  var mapOptions = {
    zoom: 6,
    center: centerLatlng,
    mapTypeId: google.maps.MapTypeId.ROADMAP,
    // disableDefaultUI: false,
    scrollwheel: true,
    // draggable: true,
    navigationControl: true,
    mapTypeControl: false,
    scaleControl: true,
    // disableDoubleClickZoom: false
  };
  var map = new google.maps.Map($("#frdo-heatmap")[0], mapOptions);
  var heatmap = new HeatmapOverlay(map, {
      "radius": 15,
      "visible": true, 
      "opacity": 40
  });
  var heatmapData = {
    min: 100, // empirical 
    max: 1500, // empirical 
    data: []
  };
  var hmFileURL = backendURL + FRDO_TEST_HEATMAP;
  
  if(hmFile) {
    hmFileURL = backendURL + FRDO_HEATMAPS + '/' + hmFile;
  }
 
  $.ajax({
    type: "GET",
    url: hmFileURL,
    dataType : "json",
    success: function(d){
      var counts = [];
      if(d) {
        console.debug(d);
        heatmapData.data = d;
        // calc min and max of counts to scale the shading (fixed seems to give a better idea of the dynamics, hence commented out)
        // for (var i = 0; i < d.length; i++) {
        //   counts.push(d[i]['count']);
        //   console.debug('Adding count:' + d[i]['count']);
        // }
        // console.debug('Counts:' + counts);
        // heatmapData.min = Math.min.apply(Math, counts);
        // heatmapData.max = Math.max.apply(Math, counts);
        console.log('Scaling heatmap with min:' + heatmapData.min + ' and max: ' + heatmapData.max);
        google.maps.event.addListenerOnce(map, "idle", function(){
            heatmap.setDataSet(heatmapData);
        });
      }
    },
    error:  function(msg){
      $("#frdo-heatmap").html("<p>There was a problem getting the heat-map data:</p><code>" + msg.responseText + "</code>");
    } 
  });
}


function getHeatmapList(){
  $.ajax({
    type: "GET",
    url: backendURL + FRDO_HEATMAPS,
    dataType : "json",
    success: function(d){
      if(d) {
        console.log('Got heatmaps: ' + d);
        for (var i = 0; i < d.length; i++) {
          heatmaps.push(d[i]);
        }
        $("#current-heatmap").html('current: ' + heatmaps[currentHeatmapPointer]);
      }
    },
    error:  function(msg){
      $("#current-heatmap").html("<p>can't load heatmaps: <code>" + msg.responseText + "</code>");
    } 
  });
}


// executes the query via JDBC
function executeQuery(){
  $('#query-results').text('not yet implemented');
}


/////////////////////////////////////////////////////
// low-level storage API using localStorage 
// check http://caniuse.com/#feat=namevalue-storage
// if your browser supports it

function _store(key, entry) {
  key += 'frdo_' + key; 
  frdostorage.setItem(key, JSON.stringify(entry));
  return key;
}

function _remove(key){
  key += 'frdo_' + key; 
  frdostorage.removeItem(key);
}

function _read(key){
  key += 'frdo_' + key; 
  return JSON.parse(frdostorage.getItem(key));
}