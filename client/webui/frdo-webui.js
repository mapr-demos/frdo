// constants
var FRDO_BACKEND_URL = 'http://localhost:6996';
var FRDO_TEST_HEATMAP = '/api/heatmap/test';
var FRDO_HEATMAPS = '/api/heatmap';
var FRDO_ALERTS = '/api/alerts'
var backendURL = FRDO_BACKEND_URL;
var GOOGLE_MAPS_BASE_URI = 'http://maps.google.com/maps?z=13&q=';

// global vars
var frdostorage = window.localStorage;
var map; // the Google map
var centerLatlng = new google.maps.LatLng(37, -40); // centre in Atlantic ocean
var mapOptions = {
  zoom: 2, // show both Americas and EMEA, make it 6 to zoom in a certain region
  center: centerLatlng,
  mapTypeId: google.maps.MapTypeId.ROADMAP,
  scrollwheel: true,
  navigationControl: true,
  mapTypeControl: false,
  scaleControl: true
  // draggable: true,
  // disableDefaultUI: false,
  // disableDoubleClickZoom: false
};
var heatmaps = []; // list of current heatmaps
var heatmapData = {}; // raw data of the heatmap as input for rendering
var heatmap; // handle to visual heatmap overlay
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
    console.debug('Current heatmap: ' + heatmaps[currentHeatmapPointer]);
    $('#current-heatmap').html('current: ' + heatmaps[currentHeatmapPointer]);
    renderHeatmap(heatmaps[currentHeatmapPointer]);
    return false;
  });
  
  $('#refresh-alerts').click(function(){
    renderAlerts();
    return false;
  });

});

// init forms
function initForms(){
  
  map = new google.maps.Map($('#frdo-heatmap')[0], mapOptions);
  
  $('#about-dialog').modal({
    backdrop: true,
    keyboard: true,
    show: false
  });
}

// init the heatmap with Google maps and render heatmaps data
function renderHeatmap(hmFile) {
  var hmFileURL = '';


  if(hmFile) {
    hmFileURL = backendURL + FRDO_HEATMAPS + '/' + hmFile;
  }
  else return;

  $.ajax({
    type: 'GET',
    url: hmFileURL,
    dataType : 'json',
    success: function(d){
      var counts = [];
      if(d) {
        console.debug(d);
        
        setCenter(d);
        map = new google.maps.Map($('#frdo-heatmap')[0], mapOptions);

        heatmapData = {
          min: 100, // empirical 
          max: 1500, // empirical 
          data: []
        };
  
        heatmap = new HeatmapOverlay(map, {
            'radius': 15,
            'visible': true, 
            'opacity': 40
        });
        
        heatmapData.data = d;
        console.log('Scaling heatmap with min:' + heatmapData.min + ' and max: ' + heatmapData.max);
        google.maps.event.addListenerOnce(map, 'idle', function(){
            heatmap.setDataSet(heatmapData);
        });
      }
    },
    error:  function(msg){
      $('#frdo-heatmap').html('<p>There was a problem getting the heat-map data:</p><code>' + msg.responseText + '</code>');
    } 
  });
}

// returns list of currently available heatmaps
function getHeatmapList(){
  $.ajax({
    type: 'GET',
    url: backendURL + FRDO_HEATMAPS,
    dataType : 'json',
    success: function(d){
      if(d) {
        console.log('Got heatmaps: ' + d);
        for (var i = 0; i < d.length; i++) {
          heatmaps.push(d[i]);
        }
        $('#current-heatmap').html('current: ' + heatmaps[currentHeatmapPointer]);
      }
    },
    error:  function(msg){
      $('#current-heatmap').html('<p>can\'t load heatmaps: <code>' + msg.responseText + '</code>');
    } 
  });
}

// returns currently available alerts
function renderAlerts(){
  $.ajax({
    type: 'GET',
    url: backendURL + FRDO_ALERTS,
    dataType : 'json',
    success: function(d){
      alist = '<h3>Alerts</h3><div>';
      if(d) {
        console.debug('Got alerts: ' + d);
        
        setCenter(d);        
        map = new google.maps.Map($('#frdo-heatmap')[0], mapOptions);

        heatmapData = {
          min: 10, 
          max: 10, 
          data: []
        };
  
        heatmap = new HeatmapOverlay(map, {
            'radius': 10,
            'visible': true, 
            'opacity': 90
        });
        
        for (var i = 0; i < d.length; i++) {
          adata = d[i];
          // http://maps.google.com/maps?z=13&q=39.211374,-82.978277
          aloc = GOOGLE_MAPS_BASE_URI + adata.lat + ',' + adata.lon;
          alist += '<div><a href="' + aloc + '" target="_new">' + adata.atm + '</a></div>';
          heatmapData.data.push({'lat': adata.lat , 'lng': adata.lon, 'count': 10});
        }
        alist += '</div>';
        $('#frdo-alerts').html(alist);
        
        console.log('Scaling heatmap with min:' + heatmapData.min + ' and max: ' + heatmapData.max);
        google.maps.event.addListenerOnce(map, 'idle', function(){
            heatmap.setDataSet(heatmapData);
        });
      }
    },
    error:  function(msg){
      $('#frdo-alerts').html('<p>can\'t load alerts: <code>' + msg.responseText + '</code>');
    } 
  });
}

// centers the map based on a list of locations
function setCenter(loclist) {
  var minlat = maxlat = minlon = maxlon = 0.0;
  var centerlat = centerlon = 0.0;
  
  if(loclist[0].transaction_id){ // we're dealing with alerts data
    minlat = maxlat = parseFloat(loclist[0].lat);
    minlon = maxlon = parseFloat(loclist[0].lon);
    for (var i = 1; i < loclist.length; i++) {
      adata = loclist[i];
      lat = parseFloat(adata.lat);
      lon = parseFloat(adata.lon);
      console.debug('lat:' + lat + '/lon:' + lon);
      if (lat < minlat) minlat = lat;
      if (lat > maxlat) maxlat = lat;
      if (lon < minlon) minlon = lon;
      if (lon > maxlon) maxlon = lon;
    }  
    mapOptions.zoom = 8;
  }   
  else { // we're dealing with heatmaps data
    minlat = maxlat = loclist[0].lat;
    minlon = maxlon = loclist[0].lng;
    for (var i = 1; i < loclist.length; i++) {
      adata = loclist[i];
      console.debug('lat:' + adata.lat + '/lon:' + adata.lng);
      if (adata.lat < minlat) minlat = adata.lat;
      if (adata.lat > maxlat) maxlat = adata.lat;
      if (adata.lng < minlon) minlon = adata.lng;
      if (adata.lng > maxlon) maxlon = adata.lng;
    }
    mapOptions.zoom = 5;
  }
  console.log('LAT min:' + minlat + ', max:' + maxlat + ' and LON min:' + minlon + ', max:' + maxlon);
  
  centerlat = (maxlat + minlat)/2;
  centerlon = (maxlon + minlon)/2;
  console.log('LAT center:' + centerlat +  ' and LON center:' + centerlon);
  
  mapOptions.center = new google.maps.LatLng(centerlat, centerlon);
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