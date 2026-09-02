import React, { useState, useEffect, useRef } from "react";

import axios from "axios";

import { Viewer, Entity, PolygonGraphics, PolylineGraphics, LabelGraphics, Camera, ImageryLayer, EllipsoidGraphics } from "resium";

import { Cartesian3, Color, Math as CesiumMath, BoundingSphere, HeadingPitchRange, UrlTemplateImageryProvider, Cartesian2, GlobeTranslucency } from "cesium";

import { Search, Layers, Play, Database, AlertTriangle, EyeOff, Navigation, ChevronRight } from "lucide-react";



import "cesium/Build/Cesium/Widgets/widgets.css";



const API_URL = "http://localhost:8000";

const TARGET_LON = 80.205000;

const TARGET_LAT = 13.085000;



const osmProvider = new UrlTemplateImageryProvider({

  url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",

  credit: "© OpenStreetMap contributors"

});



const validateCoordinate = (val: any) => {

    return typeof val === 'number' && isFinite(val) && !isNaN(val);

};



const sanitizePolygon = (coords: any[], id: string) => {

    if (!coords || !Array.isArray(coords)) {

        console.warn(`[Geometry Validation] Skipping ${id} - reason: coords is not an array`);

        return null;

    }

    if (coords.length < 6 || coords.length % 2 !== 0) {

        console.warn(`[Geometry Validation] Skipping ${id} - reason: invalid coordinate array length ${coords.length}`);

        return null;

    }

    

    let validCoords: number[] = [];

    for (let i = 0; i < coords.length; i += 2) {

        const lon = coords[i];

        const lat = coords[i + 1];

        if (!validateCoordinate(lon) || !validateCoordinate(lat)) {

            console.warn(`[Geometry Validation] Skipping ${id} - reason: NaN coordinate at index ${i}`);

            return null;

        }

        if (lon < -180 || lon > 180 || lat < -90 || lat > 90) {

            console.warn(`[Geometry Validation] Skipping ${id} - reason: coordinates out of bounds [${lon}, ${lat}]`);

            return null;

        }

        validCoords.push(lon, lat);

    }



    let deduplicated: number[] = [];

    for(let i=0; i<validCoords.length; i+=2) {

        if (deduplicated.length >= 2) {

            const prevLon = deduplicated[deduplicated.length - 2];

            const prevLat = deduplicated[deduplicated.length - 1];

            // Remove adjacent duplicates (tolerance ~1cm)

            if (Math.abs(validCoords[i] - prevLon) < 1e-7 && Math.abs(validCoords[i+1] - prevLat) < 1e-7) {

                continue;

            }

        }

        deduplicated.push(validCoords[i], validCoords[i+1]);

    }

    

    if (deduplicated.length >= 2) {

        const firstLon = deduplicated[0];

        const firstLat = deduplicated[1];

        const lastLon = deduplicated[deduplicated.length - 2];

        const lastLat = deduplicated[deduplicated.length - 1];

        // Close polygon if not closed

        if (Math.abs(firstLon - lastLon) > 1e-7 || Math.abs(firstLat - lastLat) > 1e-7) {

             deduplicated.push(firstLon, firstLat);

        }

    }



    if (deduplicated.length < 6) {

        console.warn(`[Geometry Validation] Skipping ${id} - reason: degenerate polygon with < 3 unique vertices`);

        return null;

    }



    try {

        return Cartesian3.fromDegreesArray(deduplicated);

    } catch(e) {

        console.warn(`[Geometry Validation] Cesium rejected ${id}`, e);

        return null;

    }

};



class ErrorBoundary extends React.Component<any, any> {

  constructor(props: any) {

    super(props);

    this.state = { hasError: false, errorInfo: null };

  }

  static getDerivedStateFromError(error: any) {

    return { hasError: true };

  }

  componentDidCatch(error: any, errorInfo: any) {

    console.error("ErrorBoundary caught an error", error, errorInfo);

    this.setState({ errorInfo });

  }

  render() {

    if (this.state.hasError) {

      return (

        <div className="p-6 flex flex-col items-center justify-center h-full text-center text-slate-500">

            <AlertTriangle className="text-red-500 mb-4" size={32} />

            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-widest mb-2">Unit View Error</h2>

            <p className="text-xs mb-6">Unable to display this unit.</p>

            <button onClick={() => { this.setState({ hasError: false }); this.props.onReset(); }} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded shadow transition">Return to Floor</button>

        </div>

      );

    }

    return this.props.children;

  }

}



export default function App() {

  const viewerRef = useRef<any>(null);

  const [appInitialized, setAppInitialized] = useState(false);

  const [loading, setLoading] = useState(true);



  const [parcels, setParcels] = useState<any>({ features: [] });

  const [buildings, setBuildings] = useState<any>({ features: [] });

  const [floors, setFloors] = useState<any>({ features: [] });

  const [units, setUnits] = useState<any>({ features: [] });

  const [utilities, setUtilities] = useState<any>({ features: [] });

  const [conflicts, setConflicts] = useState<any>({ features: [] });



  const [selectedBuildingId, setSelectedBuildingId] = useState<string | null>(null);

  const [activeFloor, setActiveFloor] = useState<string | null>(null);

  const [selectedUnit, setSelectedUnit] = useState<string | null>(null);

  const [exploreFloors, setExploreFloors] = useState(false);

  

  const [showUnderground, setShowUnderground] = useState(false);

  const [showConflicts, setShowConflicts] = useState(false);

  const [elevationCutoff, setElevationCutoff] = useState<number>(30); 

  

  const [searchQuery, setSearchQuery] = useState("");

  const [demoStep, setDemoStep] = useState(0);



  const [validationReport, setValidationReport] = useState<any>(null);



  useEffect(() => {

    // @ts-ignore

    window.CESIUM_BASE_URL = '/node_modules/cesium/Build/Cesium';

    

    const loadData = async () => {

      try {

        const [pRes, bRes, fRes, uRes, utilRes, cRes] = await Promise.all([

          axios.get(`${API_URL}/api/parcels`),

          axios.get(`${API_URL}/api/buildings`),

          axios.get(`${API_URL}/api/floors`),

          axios.get(`${API_URL}/api/units`),

          axios.get(`${API_URL}/api/utilities`),

          axios.get(`${API_URL}/api/conflicts`)

        ]);

        

        let report = { b:0, bValid:0, f:0, fValid:0, u:0, uValid:0, util:0, utilValid:0 };

        

        // Audit buildings

        report.b = bRes.data.features.length;

        bRes.data.features.forEach((f: any, i: number) => {

            const h = sanitizePolygon(f.geometry.coordinates[0].flat(), `Building ${f.properties.building_id || i}`);

            if (h) { report.bValid++; f._cachedHierarchy = h; }

            if (f.properties.is_primary && !h) console.error("PRIMARY DEMO BUILDING GEOMETRY INVALID");

        });



        // Audit parcels

        pRes.data.features.forEach((f: any, i: number) => {

            f._cachedHierarchy = sanitizePolygon(f.geometry.coordinates[0].flat(), `Parcel ${f.properties.parcel_id || i}`);

        });



        // Audit floors

        report.f = fRes.data.features.length;

        fRes.data.features.forEach((f: any, i: number) => {

            const h = sanitizePolygon(f.geometry.coordinates[0].flat(), `Floor ${f.properties.floor_id || i}`);

            if (h && validateCoordinate(f.properties.z_min) && validateCoordinate(f.properties.z_max)) {

                report.fValid++; f._cachedHierarchy = h;

            } else {

                console.warn(`[Geometry Validation] Skipping Floor ${f.properties.floor_id} - reason: invalid hierarchy or heights`);

            }

        });



        // Audit units

        report.u = uRes.data.features.length;

        uRes.data.features.forEach((f: any, i: number) => {

            const h = sanitizePolygon(f.geometry.coordinates[0].flat(), `Unit ${f.properties.unit_id || i}`);

            if (h && validateCoordinate(f.properties.z_min) && validateCoordinate(f.properties.z_max)) {

                report.uValid++; f._cachedHierarchy = h;

            }

        });



        // Audit utilities

        report.util = utilRes.data.features.length;

        utilRes.data.features.forEach((f: any, i: number) => {

             const coords = f.geometry.coordinates.flat();

             if (coords.length >= 4 && validateCoordinate(f.properties.z_max)) {

                  report.utilValid++;

                  f._cachedPositions = Cartesian3.fromDegreesArrayHeights([

                      coords[0], coords[1], f.properties.z_max,

                      coords[2], coords[3], f.properties.z_max

                  ]);

             } else {

                 console.warn(`[Geometry Validation] Skipping Utility ${f.properties.utility_id}`);

             }

        });



        console.log(`Geometry validation: Buildings ${report.bValid}/${report.b} valid, Floors ${report.fValid}/${report.f} valid, Units ${report.uValid}/${report.u} valid, Utilities ${report.utilValid}/${report.util} valid`);

        

        setValidationReport(report);

        setParcels(pRes.data);

        setBuildings(bRes.data);

        setFloors(fRes.data);

        setUnits(uRes.data);

        setUtilities(utilRes.data);

        setConflicts(cRes.data);

        

        setTimeout(() => setLoading(false), 800); 

        setAppInitialized(true);

      } catch (err) {

        console.error("Failed to load data", err);

        setLoading(false);

      }

    };

    loadData();

  }, []);



  useEffect(() => {

    if (appInitialized && !loading && viewerRef.current?.cesiumElement) {

      const viewer = viewerRef.current.cesiumElement;

      viewer.scene.globe.depthTestAgainstTerrain = true;

      viewer.scene.highDynamicRange = false; 

      viewer.scene.globe.showWaterEffect = false;

      viewer.scene.skyAtmosphere.show = false;

      if (viewer.scene.skyBox) viewer.scene.skyBox.show = false;

setTimeout(() => {

        const primaryBld = buildings.features?.find((f: any) => f.properties.is_primary);

        if (primaryBld) {

          flyToDemoProperty(primaryBld, 0, -45, 12.0); 

        }

      }, 500);

    }

  }, [appInitialized, loading]);



  useEffect(() => {

      if (viewerRef.current?.cesiumElement) {

          const globe = viewerRef.current.cesiumElement.scene.globe;

          if (showUnderground || demoStep >= 14) {

              if (!globe.translucency) globe.translucency = new GlobeTranslucency();

              globe.translucency.enabled = true;

              globe.translucency.frontFaceAlpha = 0.3;

              globe.translucency.backFaceAlpha = 0.3;

              globe.undergroundColor = Color.BLACK;

          } else {

              if (globe.translucency) {

                  globe.translucency.enabled = false;

              }

          }

      }

  }, [showUnderground, demoStep]);



  const getGeomBoundingSphere = (geojsonFeature: any) => {

    if (!geojsonFeature || geojsonFeature.type !== "Polygon") return null;

    const coords = geojsonFeature.coordinates[0].flat();

    const h = sanitizePolygon(coords, 'bounding-sphere');

    if (!h) return null;

    return BoundingSphere.fromPoints(h);

  };



  const flyToDemoProperty = (feature: any, headingDeg = 0, pitchDeg = -40, rangeMultiplier = 4.0, duration = 2.5) => {

    if (!viewerRef.current?.cesiumElement || !feature) return;

    const sphere = getGeomBoundingSphere(feature.geometry || feature); console.log('flyToDemoProperty bounding sphere for', feature.properties?.building_id, 'radius:', sphere?.radius, 'center:', sphere?.center);

    if (sphere && validateCoordinate(sphere.center.x) && validateCoordinate(sphere.center.y) && validateCoordinate(sphere.center.z)) {

      const range = Math.max(sphere.radius * rangeMultiplier, 50); 

      viewerRef.current.cesiumElement.camera.flyToBoundingSphere(sphere, {

        offset: new HeadingPitchRange(CesiumMath.toRadians(headingDeg), CesiumMath.toRadians(pitchDeg), range),

        duration: duration

      });

    } else {

      console.warn("[Camera] Invalid bounding sphere, aborting flyTo for", feature.properties?.unit_id || feature.properties?.building_id);

    }

  };



  const handleSearch = (e: React.FormEvent) => {

    e.preventDefault();

    const q = searchQuery.trim().toUpperCase();

    if (!q) return;



    const uMatch = units.features?.find((u: any) => u.properties.unit_id === q || u.properties.property_3d_id === q);

    if (uMatch) {

        setSelectedBuildingId(uMatch.properties.building_id);

        setExploreFloors(true);

        setActiveFloor(uMatch.properties.floor_id);

        setSelectedUnit(uMatch.properties.unit_id);

        flyToDemoProperty(uMatch, 200, -25, 2.5);

        return;

    }



    const fMatch = floors.features?.find((f: any) => f.properties.floor_id === q);

    if (fMatch) {

        setSelectedBuildingId(fMatch.properties.building_id);

        setExploreFloors(true);

        setActiveFloor(fMatch.properties.floor_id);

        setSelectedUnit(null);

        flyToDemoProperty(fMatch, 150, -30, 3.5);

        return;

    }



    const bMatch = buildings.features?.find((b: any) => b.properties.building_id === q || b.properties.demo_ulpin === q);

    if (bMatch) {

        setSelectedBuildingId(bMatch.properties.building_id);

        setExploreFloors(false);

        setActiveFloor(null);

        setSelectedUnit(null);

        flyToDemoProperty(bMatch, 45, -35, 5.0);

        return;

    }



    const pMatch = parcels.features?.find((p: any) => p.properties.parcel_id === q);

    if (pMatch) {

        const pBld = buildings.features?.find((b: any) => b.properties.parcel_id === q);

        if (pBld) {

            setSelectedBuildingId(pBld.properties.building_id);

            setExploreFloors(false);

            setActiveFloor(null);

            setSelectedUnit(null);

            flyToDemoProperty(pBld, 45, -35, 6.0);

        }

    }

  };



  const runDemoStep = (step: number) => {

    setDemoStep(step);

    if (step === 0) return;

    

    const primaryBld = buildings.features?.find((f: any) => f.properties.is_primary);

    

    setShowUnderground(false);

    setExploreFloors(false);

    setShowConflicts(false);

    setActiveFloor(null);

    setSelectedUnit(null);

    setElevationCutoff(30);



    const fly = (h: number, p: number, r: number, d = 2.5) => {

      if (primaryBld) flyToDemoProperty(primaryBld, h, p, r, d);

    };



    switch(step) {

      case 1: fly(0, -60, 50.0); break;

      case 2: fly(15, -50, 20.0); break;

      case 3: fly(30, -40, 8.0); setSelectedBuildingId("B001"); break;

      case 4: fly(45, -35, 5.0); setSelectedBuildingId("B001"); break;

      case 5: fly(60, -40, 6.0); setSelectedBuildingId("B001"); break;

      case 6: fly(75, -35, 5.5); setSelectedBuildingId("B001"); break;

      case 7: fly(90, -30, 4.5); setSelectedBuildingId("B001"); break;

      case 8: fly(120, -25, 4.0); setSelectedBuildingId("B001"); break;

      case 9: setSelectedBuildingId("B001"); setExploreFloors(true); fly(150, -20, 3.8); break;

      case 10: setSelectedBuildingId("B001"); setExploreFloors(true); fly(180, -25, 3.5); break;

      case 11: setSelectedBuildingId("B001"); setExploreFloors(true); setActiveFloor("B001-F03"); setSelectedUnit("B001-F03-U02"); fly(210, -20, 2.5, 3.0); break;

      case 12: setSelectedBuildingId("B001"); setExploreFloors(true); setActiveFloor("B001-F03"); setSelectedUnit("B001-F03-U02"); fly(240, -15, 2.5, 3.0); break;

      case 13: setSelectedBuildingId("B001"); setExploreFloors(true); setActiveFloor("B001-F03"); setSelectedUnit("B001-F03-U02"); fly(270, -10, 3.0, 3.0); break;

      case 14: setSelectedBuildingId("B001"); setElevationCutoff(0.0); setShowUnderground(true); setShowConflicts(true); fly(300, -8, 2.5, 3.0); break;

      case 15: setSelectedBuildingId("B001"); fly(0, -45, 15.0); setTimeout(() => setDemoStep(0), 4000); break;

    }

  };



  if (loading) {

    return (

      <div className="flex flex-col items-center justify-center h-screen w-screen bg-slate-900 text-white font-sans">

        <h1 className="text-2xl font-bold tracking-widest uppercase text-blue-400">3D ULPIN</h1>

        <p className="text-xs text-slate-500 mt-8 font-mono animate-pulse">Running rigorous geometry sanitization...</p>

      </div>

    );

  }



  const primaryParcel = parcels.features?.find((f: any) => f.properties.is_primary);

  const primaryBuilding = buildings.features?.find((f: any) => f.properties.is_primary);



  const selBuilding = selectedBuildingId ? buildings.features?.find((b: any) => b.properties.building_id === selectedBuildingId) : null;

  const selParcel = selBuilding ? parcels.features?.find((p: any) => p.properties.parcel_id === selBuilding.properties.parcel_id) : null;

  const selFloor = activeFloor ? floors.features?.find((f: any) => f.properties.floor_id === activeFloor) : null;

  const selUnit = selectedUnit ? units.features?.find((u: any) => u.properties.unit_id === selectedUnit) : null;



  return (

    <div className="flex flex-col h-screen w-screen bg-slate-50 text-slate-900 font-sans overflow-hidden">

      <style>{`

        .cesium-credit-logoContainer { display: none !important; }

        .cesium-credit-textContainer { font-size: 10px !important; color: #fff !important; }

      `}</style>

      

      <header className="h-14 bg-slate-900 text-white flex items-center px-6 shrink-0 shadow z-20 justify-between">

        <div className="flex items-center space-x-4">

          <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center shadow-lg"><Layers size={14} /></div>

          <div>

            <div className="font-bold tracking-widest text-sm uppercase">3D ULPIN</div>

            <div className="text-[10px] text-slate-400 font-mono">Chennai, Tamil Nadu</div>

          </div>

        </div>

        

        <form onSubmit={handleSearch} className="flex-1 max-w-xl mx-8 relative">

          <input 

            type="text" 

            value={searchQuery}

            onChange={(e) => setSearchQuery(e.target.value)}

            placeholder="Search ULPIN, Parcel, Building, Floor, or Unit ID..." 

            className="w-full bg-slate-800 border border-slate-700 text-xs font-mono rounded-full py-2 pl-10 pr-4 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition" 

          />

          <Search size={16} className="absolute left-4 top-2 text-slate-500" />

        </form>



        <button onClick={() => runDemoStep(1)} className="flex items-center space-x-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded-full shadow transition">

          <Play size={14} /><span>START SIH DEMO</span>

        </button>

      </header>



      <div className="flex flex-1 overflow-hidden relative">

        <aside className="w-64 bg-slate-50 border-r border-slate-200 flex flex-col z-10 shadow-lg shrink-0">

          <div className="p-4 space-y-5 text-sm flex-1 overflow-y-auto">

            <div className="space-y-3">

                <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-200 pb-1">Layers</h3>

                <label className="flex items-start space-x-3 cursor-pointer group">

                  <input type="checkbox" checked={true} readOnly className="mt-1 accent-blue-600" />

                  <div>

                    <div className="font-semibold text-slate-800">Real Footprints (Context)</div>

                    <div className="text-[9px] text-emerald-600 font-mono mt-0.5">REAL / OPEN DATA</div>

                  </div>

                </label>

                <label className="flex items-start space-x-3 cursor-pointer group">

                  <input type="checkbox" checked={showUnderground} onChange={(e) => setShowUnderground(e.target.checked)} className="mt-1 accent-blue-600" />

                  <div>

                    <div className="font-semibold text-slate-800">Underground Utilities</div>

                    <div className="text-[9px] text-amber-600 font-mono mt-0.5">DEMO / SYNTHETIC</div>

                  </div>

                </label>

            </div>

            

            <div className="pt-2">

               <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 border-b border-slate-200 pb-1">Vertical Section Slider</h3>

               <div className="px-2">

                 <input type="range" min="-5" max="30" step="0.5" value={elevationCutoff} onChange={(e) => {

                    const val = parseFloat(e.target.value);

                    setElevationCutoff(val);

                    if (val < 0) setShowUnderground(true);

                    else setShowUnderground(false);

                 }} className="w-full accent-blue-600" />

                 <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono font-bold">

                   <span>-5m</span><span className={elevationCutoff < 0 ? "text-amber-500" : "text-blue-600"}>{elevationCutoff.toFixed(1)}m</span><span>30m</span>

                 </div>

               </div>

            </div>

            

            <div className="pt-2 space-y-2">

              <button onClick={() => setShowConflicts(!showConflicts)} className={`w-full py-2 text-xs font-bold rounded shadow transition flex items-center justify-center space-x-2 ${showConflicts ? 'bg-red-600 text-white' : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'}`}>

                <AlertTriangle size={14} /> <span>{showConflicts ? 'Hide Conflicts' : 'Detect Conflicts'}</span>

              </button>

            </div>

          </div>

          

          <div className="p-4 bg-slate-100 border-t border-slate-200 text-xs">

            <div className="flex items-center space-x-2 text-slate-500 mb-2 font-bold"><Database size={14}/><span>DATA VALIDATION</span></div>

            <div className="text-[9px] text-slate-500 font-mono leading-tight space-y-1">

              {validationReport && (

                 <>

                   <div className={validationReport.bValid === validationReport.b ? 'text-emerald-600' : 'text-amber-600'}>Bldgs: {validationReport.bValid}/{validationReport.b} valid</div>

                   <div className={validationReport.fValid === validationReport.f ? 'text-emerald-600' : 'text-amber-600'}>Floors: {validationReport.fValid}/{validationReport.f} valid</div>

                   <div className={validationReport.uValid === validationReport.u ? 'text-emerald-600' : 'text-amber-600'}>Units: {validationReport.uValid}/{validationReport.u} valid</div>

                   <div className={validationReport.utilValid === validationReport.util ? 'text-emerald-600' : 'text-amber-600'}>Utils: {validationReport.utilValid}/{validationReport.util} valid</div>

                 </>

              )}

            </div>

          </div>

        </aside>



        <main className="flex-1 relative bg-slate-800">

          

          {demoStep > 0 && (

            <div className={`absolute z-30 bg-white/95 backdrop-blur border border-slate-200 shadow-2xl p-6 rounded-xl transition-all ${demoStep >= 14 ? "top-6 left-6 min-w-[400px]" : "top-6 left-1/2 transform -translate-x-1/2 min-w-[550px]"}`}>

              <div className="flex justify-between items-center mb-2">

                <div className="text-[10px] font-bold text-blue-600 uppercase tracking-widest">SIH Demo Sequence</div>

                <div className="text-xs font-mono bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">Step {demoStep} of 15</div>

              </div>

              <div className="font-bold text-lg text-slate-800 mb-4 h-16 flex items-center">

                {demoStep === 1 && "Start with the real Chennai urban context. 300 actual buildings."}

                {demoStep === 2 && "Zoom in on the demonstration area."}

                {demoStep === 3 && "Highlight the real building footprint."}

                {demoStep === 4 && "Explain that this footprint geometry is REAL / OPEN DATA."}

                {demoStep === 5 && "Show the synthetic cadastral parcel P000001."}

                {demoStep === 6 && "Assign Demo ULPIN: DEMO-TN-CHN-000001."}

                {demoStep === 7 && "One cadastral parcel can contain a vertically structured property."}

                {demoStep === 8 && "Extrude the real footprint into a synthetic 3D vertical model."}

                {demoStep === 9 && "Separate the model into floors (F01 - F04)."}

                {demoStep === 10 && "Show the 4 subdivided units inside each floor."}

                {demoStep === 11 && "Hierarchical Selection: F03-U02."}

                {demoStep === 12 && "Display Unique Identifier: 3D-CHN-P000001-B001-F03-U02."}

                {demoStep === 13 && "Show its explicit Z-range and calculated volume."}

                {demoStep === 14 && "Reveal underground utilities and demonstrate an intentional 3D spatial conflict."}

                {demoStep === 15 && "Review Validation: 3D SPATIAL CONFLICT DETECTED. WATER â†” SEWER overlap at -2.0m to -1.5m."}

              </div>

              <div className="flex justify-between items-center border-t border-slate-100 pt-4">

                <button onClick={() => runDemoStep(demoStep - 1)} disabled={demoStep === 1} className="text-xs px-4 py-2 text-slate-500 hover:text-slate-800 font-semibold transition disabled:opacity-30">Previous</button>

                <button onClick={() => setDemoStep(0)} className="text-xs px-4 py-2 text-red-500 hover:text-red-700 font-bold transition">Exit Demo</button>

                <button onClick={() => runDemoStep(demoStep === 15 ? 0 : demoStep + 1)} className="text-xs px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full font-bold shadow-md transition">{demoStep === 15 ? 'Finish' : 'Next →'}</button>

              </div>

            </div>

          )}



          {demoStep === 4 && (

            <div className="absolute top-1/2 left-8 transform -translate-y-1/2 z-30 bg-slate-900/95 backdrop-blur border border-slate-700 shadow-2xl p-5 rounded-xl text-white min-w-[260px]">

               <div className="text-[10px] text-emerald-400 font-mono mb-0.5">REAL / OPEN DATA</div>

               <div className="font-bold text-sm tracking-wide text-slate-200">BUILDING GEOMETRY</div>

               <div className="text-xs text-slate-400 mt-2">Source: Google Open Buildings</div>

            </div>

          )}



          {(demoStep === 12 || demoStep === 13) && (

            <div className="absolute top-1/2 left-8 transform -translate-y-1/2 z-30 bg-slate-900/95 backdrop-blur border border-slate-700 shadow-2xl p-5 rounded-xl text-white min-w-[260px]">

               <div className="text-[10px] text-amber-400 font-mono mb-1">3D PROPERTY IDENTIFIER</div>

               <div className="font-bold text-sm tracking-wide text-white mb-4 bg-slate-800 px-3 py-2 rounded">3D-CHN-P000001-B001-F03-U02</div>

               

               <div className="grid grid-cols-2 gap-4 text-xs">

                 <div><span className="text-slate-400 block mb-1">Z-MIN</span><span className="font-mono">6.4m</span></div>

                 <div><span className="text-slate-400 block mb-1">Z-MAX</span><span className="font-mono">9.6m</span></div>

                   <div className="col-span-2"><span className="text-slate-400 block mb-1">CALCULATED VOLUME</span><span className="font-mono text-emerald-400">240.0 m³</span></div>

               </div>

            </div>

          )}



          <Viewer 

            ref={viewerRef} 

            full 

            animation={false} 

            timeline={false} 

            baseLayerPicker={false} 

            infoBox={false} 

            selectionIndicator={false}

            geocoder={false} 

            homeButton={false}

            sceneModePicker={false}

            navigationHelpButton={false}

            fullscreenButton={false}

            imageryProvider={false} 

            terrainProvider={undefined}

          >

            

            <ImageryLayer imageryProvider={osmProvider} />



            {(demoStep >= 5 || demoStep === 0) && primaryParcel && primaryParcel._cachedHierarchy && (

              <Entity key="primary-parcel">

                <PolygonGraphics hierarchy={primaryParcel._cachedHierarchy} 

                                 material={Color.GOLD.withAlpha(0.05)} 

                                 outline={true} outlineColor={Color.GOLD.withAlpha(0.6)} />

              </Entity>

            )}

            

            {(demoStep >= 5 || demoStep === 0) && primaryParcel && primaryParcel._cachedHierarchy && (

              <Entity position={Cartesian3.fromDegrees(primaryParcel.geometry.coordinates[0][0][0], primaryParcel.geometry.coordinates[0][0][1], 0)}>

                 <LabelGraphics text="PARCEL\nP000001" 

                                font="bold 12px sans-serif" fillColor={Color.GOLD} 

                                showBackground={true} backgroundColor={Color.BLACK.withAlpha(0.7)}

                                pixelOffset={new Cartesian2(-20, -20)} />

              </Entity>

            )}



            {buildings.features?.map((f: any, i: number) => {

              if (!f._cachedHierarchy) return null;

              const isPrimary = f.properties.is_primary;
                const isMapped = f.properties.is_mapped;
                const isSelected = selectedBuildingId === f.properties.building_id;
                
                if (isSelected && (exploreFloors || (isPrimary && demoStep >= 7))) return null; 
                
                const h = f.properties.height;
                if (!validateCoordinate(h) || h <= 0) return null;
  
                const extH = Math.min(h, elevationCutoff);
                if (extH <= 0) return null;
                
                const bLon = f.geometry.coordinates[0][0][0];
                const bLat = f.geometry.coordinates[0][0][1];
                const dist = Math.sqrt((bLon - TARGET_LON)**2 + (bLat - TARGET_LAT)**2);
                
                let buildingColor, outlineColor;
                if (isSelected) {
                    buildingColor = Color.WHITE.withAlpha(0.95);
                    outlineColor = Color.DODGERBLUE;
                } else if (isPrimary) {
                    buildingColor = Color.WHITE.withAlpha(0.90);
                    outlineColor = Color.DODGERBLUE.withAlpha(0.8);
                } else if (isMapped) {
                    buildingColor = Color.CORNFLOWERBLUE.withAlpha(0.5);
                    outlineColor = Color.CORNFLOWERBLUE.withAlpha(0.9);
                } else if (dist < 0.002) { 
                    buildingColor = Color.SLATEGRAY.withAlpha(0.20);
                    outlineColor = Color.SLATEGRAY.withAlpha(0.10);
                } else if (dist < 0.005) { 
                    buildingColor = Color.SLATEGRAY.withAlpha(0.10);
                    outlineColor = Color.SLATEGRAY.withAlpha(0.05);
                } else { 
                    buildingColor = Color.SLATEGRAY.withAlpha(0.05);
                    outlineColor = Color.TRANSPARENT;
                }
                
                return <Entity key={`b-${i}`} onClick={() => { if(isMapped) { setSelectedBuildingId(f.properties.building_id); setExploreFloors(false); setActiveFloor(null); setSelectedUnit(null); }}}>
                  <PolygonGraphics hierarchy={f._cachedHierarchy} extrudedHeight={extH} material={buildingColor} outline={outlineColor !== Color.TRANSPARENT} outlineColor={outlineColor} />
                </Entity>;

            })}



            {(demoStep === 3 || demoStep === 4 || demoStep === 5 || demoStep === 6) && primaryBuilding && primaryBuilding._cachedHierarchy && (

              <Entity key="primary-footprint">

                <PolygonGraphics 

                  hierarchy={primaryBuilding._cachedHierarchy} 

                  material={Color.CORNFLOWERBLUE.withAlpha(0.4)} 

                  outline={true} outlineColor={Color.DODGERBLUE} />

              </Entity>

            )}



            {/* Z-Axis Visualization */}

            {(exploreFloors || demoStep >= 11 || showUnderground) && primaryBuilding && (

               (() => {

                  const bLon = primaryBuilding.geometry.coordinates[0][0][0];

                  const bLat = primaryBuilding.geometry.coordinates[0][0][1];

                  const axisLon = bLon - 0.00015;

                  const axisLat = bLat + 0.00015;

                  

                  const zMarks = [ { z: 12.8, label: "ROOF +12.8m", color: Color.WHITE, offset: -10 }, { z: 9.6, label: "F04  +9.6m", color: Color.LIGHTSKYBLUE, offset: -10 }, { z: 6.4, label: "F03  +6.4m", color: Color.LIGHTSKYBLUE, offset: -10 }, { z: 3.2, label: "F02  +3.2m", color: Color.LIGHTSKYBLUE, offset: -10 }, { z: 0.0, label: "GROUND 0.0m", color: Color.LIGHTGREEN, offset: -10 } ]; if (showUnderground || demoStep >= 14 || elevationCutoff < 0) { zMarks.push({ z: -1.0, label: "SEWER -1.0 to -2.0m", color: Color.ORANGE, offset: -60 }); zMarks.push({ z: -2.5, label: "WATER -1.5 to -2.5m", color: Color.DODGERBLUE, offset: -60 }); }

                  

                  const axisPositions = Cartesian3.fromDegreesArrayHeights([

                      axisLon, axisLat, (showUnderground || demoStep >= 14) ? -3.0 : 0.0,

                      axisLon, axisLat, 13.5

                  ]);



                  return (

                      <React.Fragment key="z-axis">

                          <Entity>

                              <PolylineGraphics positions={axisPositions} width={2} material={Color.WHITE.withAlpha(0.5)} />

                          </Entity>

                          {zMarks.map((mark, i) => (

                              <React.Fragment key={`zmark-${i}`}>

                                  <Entity position={Cartesian3.fromDegrees(axisLon, axisLat, mark.z)}>

                                      <EllipsoidGraphics radii={new Cartesian3(0.5, 0.5, 0.5)} material={mark.color} />

                                  </Entity>

                                  <Entity position={Cartesian3.fromDegrees(axisLon - 0.00002, axisLat, mark.z)}>

                                      <LabelGraphics 

                                          text={mark.label} 

                                          font="bold 10px monospace" 

                                          fillColor={mark.color} 

                                          showBackground={true} 

                                          backgroundColor={Color.BLACK.withAlpha(0.7)}

                                          horizontalOrigin={2} // RIGHT

                                          pixelOffset={new Cartesian2(mark.offset, 0)}

                                          disableDepthTestDistance={Number.POSITIVE_INFINITY}

                                      />

                                  </Entity>

                              </React.Fragment>

                          ))}

                      </React.Fragment>

                  );

               })()

            )}



            {(exploreFloors || (demoStep >= 7 && demoStep <= 13) || (demoStep === 0 && selectedBuildingId)) && floors.features?.filter((f: any) => f.properties.building_id === (demoStep >= 7 && demoStep <= 13 ? 'B001' : selectedBuildingId)).map((f: any, i: number) => {

              if (!f._cachedHierarchy) return null;

              const v = f.properties;

              

              const isSelected = activeFloor === v.floor_id;

              const isDimmed = activeFloor !== null && !isSelected;

              

              const gapSize = exploreFloors ? 0.8 : 0.0; 

              const floorOffset = i * gapSize;

              

              let z_min = v.z_min + floorOffset;

              let z_max = v.z_max + floorOffset; 

              

              if (z_min > elevationCutoff) return null;

              z_max = Math.min(z_max, elevationCutoff);

              if (z_max <= z_min) return null;

              if (!validateCoordinate(z_min) || !validateCoordinate(z_max)) return null;



              const color = isSelected ? Color.DODGERBLUE.withAlpha(0.4) : (isDimmed ? Color.SLATEGRAY.withAlpha(0.15) : Color.WHITE.withAlpha(0.95));

              const outColor = isSelected ? Color.WHITE : (isDimmed ? Color.SLATEGRAY.withAlpha(0.4) : Color.SLATEGRAY.withAlpha(0.7));

              

              return (

                <Entity key={`f-${i}`} onClick={() => { setActiveFloor(v.floor_id); setSelectedUnit(null); }}>

                    <PolygonGraphics hierarchy={f._cachedHierarchy} height={z_min} extrudedHeight={z_max} material={color} outline={true} outlineColor={outColor} />

                </Entity>

              );

            })}



            {(demoStep >= 10 || (exploreFloors && activeFloor)) && units.features?.filter((f: any) => f.properties.building_id === (demoStep >= 7 && demoStep <= 13 ? 'B001' : selectedBuildingId)).map((f: any, i: number) => {

              if (!f._cachedHierarchy) return null;

              const v = f.properties;

              

              const isFloorSelected = activeFloor === v.floor_id;

              const isUnitSelected = selectedUnit === v.unit_id;

              

              if (demoStep < 10 && activeFloor && !isFloorSelected) return null;



              const isDimmed = selectedUnit !== null && !isUnitSelected;

              

              const floorIndex = parseInt(v.floor_id.split('-F')[1]) - 1;

              const floorOffset = floorIndex * (exploreFloors ? 0.8 : 0.0);

              

              let z_min = v.z_min + floorOffset;

              let z_max = v.z_max + floorOffset;

              

              if (z_min > elevationCutoff) return null;

              z_max = Math.min(z_max, elevationCutoff);

              if (z_max <= z_min) return null;

              if (!validateCoordinate(z_min) || !validateCoordinate(z_max)) return null;



              let unitColor = Color.CYAN.withAlpha(0.3);

              let outlineColor = Color.WHITE.withAlpha(0.8);

              let labelColor = Color.WHITE;

              let labelBg = Color.BLACK.withAlpha(0.6);

              

              if (isDimmed) {

                  unitColor = Color.SLATEGRAY.withAlpha(0.1);

                  outlineColor = Color.SLATEGRAY.withAlpha(0.3);

                  labelColor = Color.GRAY;

                  labelBg = Color.BLACK.withAlpha(0.3);

              }

              if (isUnitSelected) {

                  unitColor = Color.GOLD.withAlpha(0.7);

                  outlineColor = Color.WHITE;

                  labelBg = Color.GOLD.withAlpha(0.9);

                  labelColor = Color.BLACK;

              }

              

              // Calculate rough centroid for label

              const coords = f.geometry.coordinates[0];

              let sumX = 0, sumY = 0;

              for(let k=0; k<coords.length; k++) {

                  sumX += coords[k][0];

                  sumY += coords[k][1];

              }

              const midLon = sumX / coords.length;

              const midLat = sumY / coords.length;

              const unitShortId = v.unit_id.split('-').pop();

              

              return (

                <React.Fragment key={`u-${i}`}>

                  <Entity onClick={() => { setActiveFloor(v.floor_id); setSelectedUnit(v.unit_id); }}>

                    <PolygonGraphics 

                        hierarchy={f._cachedHierarchy} 

                        height={z_min} 

                        extrudedHeight={z_max} 

                        material={unitColor} 

                        outline={true} 

                        outlineColor={outlineColor} 

                        outlineWidth={3}

                    />

                  </Entity>

                  {(!isDimmed || isUnitSelected) && (

                      <Entity position={Cartesian3.fromDegrees(midLon, midLat, z_max + 0.2)}>

                         <LabelGraphics 

                             text={unitShortId} 

                             font="bold 12px monospace" 

                             fillColor={labelColor} 

                             showBackground={true} 

                             backgroundColor={labelBg}

                             pixelOffset={new Cartesian2(0, 0)}

                             disableDepthTestDistance={Number.POSITIVE_INFINITY}

                         />

                      </Entity>

                  )}

                </React.Fragment>

              );

            })}



            {(showUnderground || demoStep >= 14) && utilities.features?.map((f: any, i: number) => {

              if (!f._cachedPositions) return null;

              let typeColor = f.properties.type === 'WATER' ? Color.DODGERBLUE : (f.properties.type === 'SEWER' ? Color.BROWN : Color.GOLD);

              if (demoStep === 14) typeColor = typeColor.withAlpha(0.25);



              const coords = f.geometry.coordinates.flat();

              const midLon = (coords[0] + coords[2]) / 2;

              const midLat = (coords[1] + coords[3]) / 2;



              return (

                  <React.Fragment key={`util-${i}`}>

                      <Entity>

                        <PolylineGraphics positions={f._cachedPositions} width={12} material={typeColor} />

                      </Entity>

                      <Entity position={Cartesian3.fromDegrees(midLon, midLat, f.properties.z_max + 0.5)}>

                         <LabelGraphics text={`${f.properties.type}

${f.properties.z_min.toFixed(1)}m`} 

                                        font="bold 10px monospace" fillColor={Color.WHITE} 

                                        showBackground={true} backgroundColor={typeColor.withAlpha(0.9)} />

                      </Entity>

                  </React.Fragment>

              );

            })}



            {/* CONFLICT HIGHLIGHT */}

            {showConflicts && conflicts.features?.map((f: any, i: number) => {

               const p = f.geometry.coordinates;

               if (!p || p.length < 2) return null;

               return (

                  <React.Fragment key={`conflict-${i}`}>

                      <Entity position={Cartesian3.fromDegrees(p[0], p[1], -1.75)}>

                          <EllipsoidGraphics radii={new Cartesian3(2.5, 2.5, 2.5)} material={Color.RED.withAlpha(0.7)} outline={true} outlineColor={Color.RED} />

                      </Entity>

                      <Entity position={Cartesian3.fromDegrees(p[0], p[1], -0.2)}>

                          <LabelGraphics text={`3D SPATIAL CONFLICT

WATER ↔ SEWER

Z OVERLAP: -2.0m to -1.5m`} font="bold 12px monospace" fillColor={Color.WHITE} showBackground={true} backgroundColor={Color.RED.withAlpha(0.9)} pixelOffset={new Cartesian2(0, -40)} disableDepthTestDistance={Number.POSITIVE_INFINITY} />

                      </Entity>

                  </React.Fragment>

               );

            })}

          </Viewer>

        </main>



        {(selBuilding) && (

          <aside className="w-[340px] bg-white border-l border-slate-200 flex flex-col z-10 shadow-2xl shrink-0 overflow-y-auto">

            {/* BUILDING VIEW */}

            {!selFloor && !selUnit && (

                <>

                <div className="p-4 bg-slate-900 text-white flex justify-between items-center shadow-md">

                  <h2 className="text-xs font-bold tracking-widest uppercase">Property Inspector</h2>

                  <button onClick={() => { setSelectedBuildingId(null); setActiveFloor(null); setSelectedUnit(null); }} className="text-slate-400 hover:text-white transition"><EyeOff size={16}/></button>

                </div>

                

                <div className="p-5 flex-1 text-sm space-y-6">

                  <div className="border border-slate-200 rounded-lg overflow-hidden">

                    <div className="bg-slate-50 p-3 border-b border-slate-200">

                        <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-0.5">DEMO ULPIN</div>

                        <div className="font-mono text-xl font-bold text-slate-900">{selBuilding.properties.demo_ulpin}</div>

                        <div className="text-[9px] font-mono font-bold bg-amber-100 text-amber-700 px-2 py-1 rounded inline-block mt-2">DATA STATUS: DEMO / SYNTHETIC</div>

                    </div>

                    

                    <div className="p-3 border-b border-slate-200">

                        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">CADASTRAL PARCEL</h3>

                        <div className="flex justify-between items-center mb-1"><span className="text-xs text-slate-500">Parcel ID:</span><span className="text-xs font-mono font-bold">{selBuilding.properties.parcel_id}</span></div>

                        <div className="flex justify-between items-center mb-1"><span className="text-xs text-slate-500">Parcel Area:</span><span className="text-xs font-mono">{selParcel ? selParcel.properties.area_sqm.toFixed(2) : '-'} m²</span></div>

                    </div>



                    <div className="p-3 border-b border-slate-200">

                        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">BUILDING</h3>

                        <div className="flex justify-between items-center mb-1"><span className="text-xs text-slate-500">Building ID:</span><span className="text-xs font-mono font-bold">{selBuilding.properties.building_id}</span></div>

                        <div className="text-[9px] font-mono font-bold bg-emerald-100 text-emerald-700 px-2 py-1 rounded inline-block mb-1 mt-1">REAL / OPEN DATA</div>

                        <div className="text-xs text-slate-600 font-semibold">Source: {selBuilding.properties.source}</div>

                    </div>



                    <div className="p-3 border-b border-slate-200">

                        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">VERTICAL MODEL</h3>

                        <div className="flex justify-between items-center mb-1"><span className="text-xs text-slate-500">Floors:</span><span className="text-xs font-mono font-bold">{selBuilding.properties.floors}</span></div>

                        <div className="text-[9px] font-mono font-bold bg-amber-100 text-amber-700 px-2 py-1 rounded inline-block mt-1">DEMO / SYNTHETIC</div>

                    </div>

                    

                    <div className="p-3 bg-slate-50">

                        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">3D PROPERTY UNITS</h3>

                        <div className="flex justify-between items-center mb-1"><span className="text-xs text-slate-500">Total Units:</span><span className="text-xs font-mono font-bold">{selBuilding.properties.floors * 4}</span></div>

                        <div className="flex justify-between items-center"><span className="text-xs text-slate-500">Units per floor:</span><span className="text-xs font-mono">4</span></div>

                    </div>

                  </div>



                  <button onClick={() => { setExploreFloors(true); setActiveFloor(null); }} className="w-full py-2 text-xs font-bold rounded border shadow-sm transition flex items-center justify-center space-x-2 bg-indigo-600 text-white hover:bg-indigo-700">

                      <Navigation size={14} /> <span>Explore Floors</span>

                  </button>

                </div>

                </>

            )}



            {/* FLOOR VIEW */}

            {selFloor && !selUnit && (

                <>

                <div className="p-4 bg-slate-900 text-white flex justify-between items-center shadow-md">

                  <div className="flex items-center space-x-2 cursor-pointer hover:text-blue-300 transition" onClick={() => setActiveFloor(null)}>

                     <ChevronRight className="rotate-180" size={16} />

                     <h2 className="text-xs font-bold tracking-widest uppercase">FLOOR {selFloor.properties.floor_id.split('-')[1]}</h2>

                  </div>

                  <button onClick={() => { setSelectedBuildingId(null); setActiveFloor(null); setSelectedUnit(null); }} className="text-slate-400 hover:text-white transition"><EyeOff size={16}/></button>

                </div>

                

                <div className="p-5 flex-1 text-sm space-y-6">

                  <div className="border border-slate-200 rounded-lg overflow-hidden">

                    <div className="bg-slate-50 p-3 border-b border-slate-200">

                        <div className="text-[10px] text-slate-400 uppercase tracking-wider mb-0.5">Floor ID</div>

                        <div className="font-mono text-xl font-bold text-slate-900">{selFloor.properties.floor_id}</div>

                    </div>

                    

                    <div className="p-3 border-b border-slate-200 space-y-2">

                        <div className="flex justify-between items-center"><span className="text-xs text-slate-500">Parent Parcel:</span><span className="text-xs font-mono font-bold cursor-pointer text-blue-600" onClick={() => { setActiveFloor(null); }}>{selFloor.properties.parcel_id}</span></div>

                        <div className="flex justify-between items-center"><span className="text-xs text-slate-500">Building:</span><span className="text-xs font-mono font-bold cursor-pointer text-blue-600" onClick={() => { setActiveFloor(null); }}>{selFloor.properties.building_id}</span></div>

                    </div>



                    <div className="p-3 border-b border-slate-200">

                        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Z RANGE</h3>

                        <div className="font-mono text-lg font-bold text-slate-800">{selFloor.properties.z_min.toFixed(1)}m ↔ {selFloor.properties.z_max.toFixed(1)}m</div>

                    </div>



                    <div className="p-3 bg-slate-50">

                        <div className="text-[9px] font-mono font-bold bg-amber-100 text-amber-700 px-2 py-1 rounded inline-block">DATA STATUS: DEMO / SYNTHETIC</div>

                    </div>

                  </div>

                  

                  <div>

                      <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 border-b border-slate-200 pb-2">Units (4)</h3>

                      <div className="grid grid-cols-2 gap-2">

                          {units.features?.filter((u: any) => u.properties.floor_id === selFloor.properties.floor_id).map((u: any) => (

                             <button key={u.properties.unit_id} onClick={() => setSelectedUnit(u.properties.unit_id)} className="py-2 bg-white border border-slate-200 hover:border-blue-500 hover:bg-blue-50 text-slate-800 font-mono text-sm font-bold rounded shadow-sm transition">

                                 {u.properties.unit_id.split('-').pop()}

                             </button>

                          ))}

                      </div>

                  </div>

                </div>

                </>

            )}



            {/* UNIT VIEW */}

            {selUnit && (

                <ErrorBoundary onReset={() => setSelectedUnit(null)}>

                <div className="p-4 bg-slate-900 text-white flex justify-between items-center shadow-md">

                  <div className="flex items-center space-x-2 cursor-pointer hover:text-blue-300 transition" onClick={() => setSelectedUnit(null)}>

                     <ChevronRight className="rotate-180" size={16} />

                     <h2 className="text-xs font-bold tracking-widest uppercase">3D PROPERTY UNIT</h2>

                  </div>

                  <button onClick={() => { setSelectedBuildingId(null); setActiveFloor(null); setSelectedUnit(null); }} className="text-slate-400 hover:text-white transition"><EyeOff size={16}/></button>

                </div>

                

                <div className="p-5 flex-1 text-sm space-y-4">

                  

                  <div className="bg-slate-800 text-white p-3 rounded-lg shadow-inner">

                      <div className="text-[10px] text-blue-300 font-mono mb-1">3D PROPERTY ID</div>

                      <div className="font-mono text-sm font-bold tracking-tight break-all">{selUnit.properties.property_3d_id}</div>

                  </div>



                  <div className="border border-slate-200 rounded-lg overflow-hidden">

                    <div className="p-3 border-b border-slate-200 bg-slate-50">

                        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">PARENT PROPERTY</h3>

                        <div className="space-y-1">

                            <div className="flex justify-between items-center"><span className="text-xs text-slate-500">ULPIN:</span><span className="text-[10px] font-mono">{selUnit.properties.demo_ulpin}</span></div>

                            <div className="flex justify-between items-center"><span className="text-xs text-slate-500">Parcel:</span><span className="text-xs font-mono font-bold cursor-pointer text-blue-600" onClick={() => { setActiveFloor(null); setSelectedUnit(null); }}>{selUnit.properties.parcel_id}</span></div>

                            <div className="flex justify-between items-center"><span className="text-xs text-slate-500">Building:</span><span className="text-xs font-mono font-bold cursor-pointer text-blue-600" onClick={() => { setActiveFloor(null); setSelectedUnit(null); }}>{selUnit.properties.building_id}</span></div>

                            <div className="flex justify-between items-center"><span className="text-xs text-slate-500">Floor:</span><span className="text-xs font-mono font-bold cursor-pointer text-blue-600" onClick={() => { setSelectedUnit(null); }}>{selUnit.properties.floor_id}</span></div>

                            <div className="flex justify-between items-center"><span className="text-xs text-slate-500">Unit:</span><span className="text-xs font-mono font-bold text-slate-800">{selUnit.properties.unit_id}</span></div>

                        </div>

                    </div>



                    <div className="p-3 border-b border-slate-200">

                        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">VERTICAL EXTENT</h3>

                        <div className="flex justify-between items-center mb-1"><span className="text-xs text-slate-500">Z MIN:</span><span className="text-xs font-mono font-bold">{selUnit.properties.z_min?.toFixed(1) ?? '-'} m</span></div>

                        <div className="flex justify-between items-center mb-1"><span className="text-xs text-slate-500">Z MAX:</span><span className="text-xs font-mono font-bold">{selUnit.properties.z_max?.toFixed(1) ?? '-'} m</span></div>

                        <div className="flex justify-between items-center"><span className="text-xs text-slate-500">HEIGHT:</span><span className="text-xs font-mono text-emerald-600 font-bold">{selUnit.properties.height?.toFixed(1) ?? '-'} m</span></div>

                    </div>



                    <div className="p-3 border-b border-slate-200">

                        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">SPATIAL METRICS</h3>

                        <div className="flex justify-between items-center mb-1"><span className="text-xs text-slate-500">Footprint Area:</span><span className="text-xs font-mono font-bold">{selUnit.properties.area_sqm?.toFixed(1) ?? '-'} m²</span></div>

                        <div className="flex justify-between items-center"><span className="text-xs text-slate-500">3D Volume:</span><span className="text-xs font-mono text-indigo-600 font-bold">{selUnit.properties.volume_m3?.toFixed(1) ?? '-'} m³</span></div>

                    </div>

                    

                    <div className="p-3 bg-slate-50 space-y-2">

                        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">DATA PROVENANCE</h3>

                        <div className="flex justify-between items-center"><span className="text-[10px] font-bold text-slate-600">REAL FOOTPRINT</span><span className="text-[9px] font-mono font-bold bg-emerald-100 text-emerald-700 px-1 py-0.5 rounded">REAL / OPEN DATA</span></div>

                        <div className="flex justify-between items-center"><span className="text-[10px] font-bold text-slate-600">VERTICAL EXTENT</span><span className="text-[9px] font-mono font-bold bg-amber-100 text-amber-700 px-1 py-0.5 rounded">DEMO / SYNTHETIC</span></div>

                        <div className="flex justify-between items-center"><span className="text-[10px] font-bold text-slate-600">UNIT BOUNDARY</span><span className="text-[9px] font-mono font-bold bg-amber-100 text-amber-700 px-1 py-0.5 rounded">DEMO / SYNTHETIC</span></div>

                        <div className="flex justify-between items-center"><span className="text-[10px] font-bold text-slate-600">OWNERSHIP</span><span className="text-[9px] font-mono font-bold bg-amber-100 text-amber-700 px-1 py-0.5 rounded">DEMO / SYNTHETIC</span></div>

                    </div>

                  </div>

                </div>

                </ErrorBoundary>

            )}

          </aside>

        )}

      </div>



      <footer className="h-6 bg-slate-900 border-t border-slate-800 text-[9px] text-slate-400 flex items-center px-4 shrink-0 justify-between font-mono">

        <div className="flex space-x-4">

          <span className="flex items-center space-x-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 block"></span><span>System Online</span></span>

          <span>Lat: 13.085000</span>

          <span>Lon: 80.205000</span>

          <span>CRS: EPSG:4326</span>

          <span>Data: Safe GeoJSON</span>

        </div>

      </footer>

    </div>

  );

}













