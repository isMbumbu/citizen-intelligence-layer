# Geography specification

The project explorer uses the deliberately small hierarchy County → SubCounty
→ Ward → Project. Each level has a stable UUID and a parent foreign key. The
vertical slice stores only the places required by the demonstration dataset;
it does not claim to be a complete Kenyan administrative register.

Project records reference a ward and expose its county, sub-county, and ward in
API responses. Boundary geometry and spatial querying are out of scope for
this slice, so PostGIS is not used until a geographic feature requires it.
