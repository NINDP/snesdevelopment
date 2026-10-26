# Cinematic source assets

`OpeningGymScene.png`, Kirill sprites and coin frames come from the local
Novgu-Biohazard project. Its MIT notice is included as `Novgu-Biohazard.LICENSE`.

`basement.png` and `arrival.png` were generated with the built-in image_gen tool,
using the first game's pixel art and Kirill sprite as visual references.
The build converts these source images to indexed 4bpp tiles and SNES palettes.

## Basement prompt

Use case: illustration-story. Asset type: production background for a 256x224 SNES horror game, cinematic playable prologue frame. Reference image 1 is the pixel art visual style of the first game, reference image 2 is the protagonist Kirill's exact recognizable design, reference image 3 is a university stairwell material/mood reference. Create ONE wide landscape 16:9 pixel-art scene: looking down a gloomy university basement staircase, rough damp gray plaster, worn stone steps descending toward a half-open wooden cellar door, three faint carved circles on its lintel, a small silver coin glowing pale amber on a step near the door. Young Kirill in his recognizable charcoal jacket and dark blue trousers, small full-body figure seen from behind halfway down the steps, one hand on the railing. Cinematic composition, strong perspective, teal blue shadows, restrained warm amber pool of light from the open door, subtle moisture reflections, atmospheric darkness but readable silhouette and architecture. Authentic meticulous hand-placed pixel art, coherent crisp pixel clusters, designed to remain legible when downsampled to 256x144. Match the first game references' restrained detailed 16-bit pixel rendering. The illustrated scene occupies the top two thirds and middle; bottom quarter very dark and quiet for a separate game dialogue overlay. No words, no letters, no logo, no UI, no borders, no watermark. This is game background artwork, not an emulator screenshot or mockup.

## Arrival prompt

Use case: illustration-story. Asset type: one production cutscene illustration for a SNES horror game. Reference image 1 gives the first game's detailed restrained pixel-art style; reference image 2 is modern student Kirill, whose consciousness has entered another body. Create ONE wide landscape 16:9 cinematic pixel-art frame: ancient northern Russian riverside village at night, 1193, timber houses in distant mist, dark fir forest, a modest small wooden chapel with a simple cross far behind. Foreground right: a young medieval boatbuilder Vsevolod, rugged dark shoulder-length hair, simple muted brown wool tunic, kneeling at black river water holding a small hooded oil lantern. His physical face is unfamiliar and bearded. In the water directly below his face the reflection instead shows modern clean-shaven student Kirill with short brown hair and charcoal jacket from reference 2. The mismatched reflection is the clear focal point, an immediately understandable supernatural body-swap reveal. Warm amber lantern on face and hands, blue-green river and forest, moonlit mist, carefully composed cinematic silhouette, high contrast readable at 256x144 pixels, authentic coherent meticulous hand-drawn 16-bit pixel-art clusters, no smooth painterly brushwork. Keep lower quarter dark and simple for a game text overlay. No words, no UI, no labels, no borders, no watermark. Only this scene, not a collage. This artwork must be used inside the actual game.

## Playable location artwork

The four location backgrounds were also generated with the built-in image_gen
tool, using the previous maps as geometry guides and arrival.png as the style
reference. Runtime actors and interactions are drawn by the game.

### village

Use case: stylized-concept. Asset type: actual playable SNES top-down village background, one screen, 256x224 game coordinate grid. Image 1 is a STRICT level geometry reference, preserve its exact overhead orthographic camera, building footprints, positions and paths. Image 2 is the established artistic style and palette reference. Repaint image 1 into rich coherent exquisite 16-bit pixel art of medieval northern Russian Chornorechye village at night: two timber houses occupy ONLY upper-left rectangle (14,30)-(84,63) and upper-right rectangle (157,30)-(235,68), a dark river and little wooden landing stay at upper center (90,26)-(146,77), damp blue earth and sparse grass, weathered logs, amber window glows, fences along bottom y184, wooden grave marker at (32,146), oil jug at (116,158), a small empty luminescent memory trace at (94,104), exit gate at right (232,152). Preserve a broad clear WALKABLE open courtyard everywhere else, including clear routes near (56,78) and (190,112). No people, no enemies, no player, no characters. No text, symbols like letters, HUD or labels. Keep top 24 pixels and bottom 32 pixels quiet/dark as in geometry reference. Orthographic overhead map, NOT perspective landscape, NOT isometric. Actual finely detailed production pixel art with readable clusters when reduced to 256x224, restrained teal-blue shadows, warm muted amber accents, believable wet stones and grass, no excessive noise. The level layout and object locations must match image 1, with image 2 used only for art direction. No UI, no watermark.

### forest

Use case: stylized-concept. Asset type: actual single-screen SNES top-down forest map, 256x224 game coordinate grid. Image 1 is a STRICT geometry reference: preserve exact overhead orthographic camera and all clear paths and object coordinates. Image 2 is only artistic style/color reference. Repaint image 1 into detailed coherent beautiful 16-bit pixel art of dark medieval Russian fir forest by a black ford: narrow river strip along left x8..44,y24..128, small wooden bridge near (30,144), tall layered firs at the exact positions of the reference, clear winding earth trail across middle. Important inspectable places must remain unobstructed and readable at: birch parchment on stump (64,96), EMPTY glade for NPC (184,76), water marker (28,144), family-tree rune stone (116,60), extinguished campfire light marker (208,144), trail exit to chapel at right (232,102), oil jar (128,166), old boat plank (80,158), blue-green circular reflection (168,116), return opening at top-left (12,40). Add rich bark, moss, roots, damp fern edges and small pebbles along edges, deep teal forest, blue-green water, restrained amber highlights. Top 24 and bottom 32 pixels quiet/dark. Do not add buildings, people or creatures. No text or labels or HUD. Camera straight overhead, NOT isometric, NOT a perspective view. Keep the center and existing trail WALKABLE, don't obstruct it with trees. Crisp production pixel clusters readable at 256x224, no smooth painterly texture, no watermark.

### chapel

Use case: stylized-concept. Asset type: actual playable SNES orthographic top-down wooden chapel interior background, one 256x224 game coordinate screen. Image 1 is the STRICT geometry reference; preserve exact object positions, footprints and walkable floors. Image 2 supplies only artistic direction/colors. Repaint image 1 as beautiful atmospheric coherent 16-bit pixel art: modest medieval Russian timber chapel, dark worn plank floor, carved simple timber posts at left/right edges, amber candles, modest wooden cross at upper center, altar/cup table at (128,66), bench left around (30,100) and bench right around (225,100), EMPTY NPC standing spaces at (48,88) and (198,88), silver disk on small stand at (84,124), three small hanging signal bells at (158,142),(172,142),(186,142), old book low-left at (36,150), oil lamp vessel at (126,158), stair opening down at bottom-right (228,170), small rear door at (224,48). Preserve clear walkable center and all existing paths. Delicate amber illumination on wood, dark blue and muted brown shadows, restrained small candle glow, rich hand-placed pixel clusters, no perspective distortion, NOT isometric, no modern church grandeur. Keep dark quiet 24-pixel top and 32-pixel bottom margins. No people, no enemies, no text, no HUD, no watermark. Must read as an actual 16-bit game level, not a landscape painting.

### cellar

Use case: stylized-concept. Asset type: actual single-screen SNES orthographic top-down horror cellar level background, coordinate canvas 256x224. Image 1 is a STRICT geometry guide: preserve exact camera, object coordinates, clear paths and basic layout. Image 2 supplies only detailed restrained 16-bit pixel art style and color mood. Repaint image 1 as an ancient damp stone cellar below a medieval wooden chapel. Three small rune plinths in a horizontal row centered at (48,130),(128,130),(208,130). Black Heart stone over a small round black fissure centered at (128,66). Surrounding thin engraved ritual circle on floor from (88,100) to (168,172). Old stone recesses line top wall y26..46. Old carved stone at (56,84), EMPTY space for ghost NPC at (192,82), small luminous hand trace at (84,96), oil jar at (24,170), exit stairs at (232,170). Wet dark slate tile floor, moss in cracks, eroded masonry, tiny burgundy/red glow inside heart fissure, dim amber lamps, teal-blue shadows, restrained gold rune accents. Keep broad central and lower corridors WALKABLE exactly as in reference. Do not place extra obstacles. Top 24 pixels and bottom 32 pixels quiet/dark. No people, no player, no monsters, no text or labels, no HUD, no watermark. Straight overhead 2D game map, NOT perspective landscape and NOT isometric. Meticulous clear pixel clusters that will survive conversion to SNES tiles at 256x224.
## Torch revision

`arrival-torch.png` is a non-destructive built-in image_gen edit of arrival.png.
Gameplay flame frames, ember pixels and the unlit shaft are authored in
build_assets.py and exported as assets/generated/torch-sheet.png.

Edit target: image 1, the existing pixel-art Chornorechye body-swap river scene. Change ONLY the medieval man's handheld lantern into a burning wooden TORCH. His hand must grip a dark wrapped wooden torch shaft in the exact location of the old lantern handle, with a lively orange-gold flame, a few small rising ember pixels, and a little heat shimmer immediately over the flame. Preserve the character, his pose, the reflected modern Kirill, all composition, village, chapel, trees, river, moon, pixel-art style, crop and color palette. Keep the existing warm light pool and reflection on water, now originating from the torch. No lantern remains. No new text, no labels, no UI, no watermark. Output the complete edited scene.

## Corridor and running frames

`Scene2Corridor.png` and `SceneTwoMainCharacterRunRight2..7.png` are copied
unchanged from `alman790/Novgu-Biohazard`, commit
`21c43ed11999af7799ee3b2488d9f261b37179b2`, `assets/source/`.
The existing MIT notice covers these assets. Together with OpeningGymScene
they form one 512-pixel panorama. All seven original running poses are
converted into the OBJ atlas; camera scroll and stair movement are runtime code.
The title backdrop is drawn in build_assets.py following the first game's
MenuScene composition: warm light on the left, dark city silhouettes on the right.
