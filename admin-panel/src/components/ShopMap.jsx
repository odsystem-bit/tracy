import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const shopIcon = L.divIcon({
  className: 'custom-marker',
  iconSize: [14, 14],
  iconAnchor: [7, 7],
})

export default function ShopMap({ shops = [], height = '400px', showPopups = true, zoom = 6 }) {
  const center = shops.length > 0
    ? [shops[0].latitude, shops[0].longitude]
    : [9.3077, 2.3158] // Bénin par défaut

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height, width: '100%', borderRadius: '0.75rem' }}
      scrollWheelZoom
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap'
      />
      {shops.filter(s => s.latitude && s.longitude).map((shop, i) => (
        <Marker key={shop.id || i} position={[shop.latitude, shop.longitude]} icon={shopIcon}>
          {showPopups && (
            <Popup>
              <div className="min-w-[180px]">
                <p className="font-semibold text-slate-900">{shop.shop_name || shop.name || 'Boutique'}</p>
                <p className="text-xs text-slate-500 mt-0.5">{shop.country || '—'}</p>
                <div className="mt-2 space-y-1 text-xs">
                  <p><span className="text-slate-400">Vendeur:</span> {shop.vendor_name || shop.name || '—'}</p>
                  <p><span className="text-slate-400">Plan:</span> {shop.bot_plan || 'free'}</p>
                  <p><span className="text-slate-400">Produits:</span> {shop.product_count || 0}</p>
                  <p><span className="text-slate-400">KYC:</span> {shop.kyc_status || 'pending'}</p>
                </div>
              </div>
            </Popup>
          )}
        </Marker>
      ))}
    </MapContainer>
  )
}
