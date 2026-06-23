import { useEffect } from "react";
import { useMapEvents, useMap } from "react-leaflet";

export function MapClickHandler({ activo, onClick }) {
  useMapEvents({
    click(e) {
      if (activo) onClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export function MapResize() {
  const map = useMap();
  useEffect(() => {
    const fix = () => map.invalidateSize({ animate: false });
    fix();
    const t1 = setTimeout(fix, 100);
    const t2 = setTimeout(fix, 500);
    window.addEventListener("resize", fix);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      window.removeEventListener("resize", fix);
    };
  }, [map]);
  return null;
}
