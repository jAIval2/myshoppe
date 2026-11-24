// written by silhouette/parts/build_layers.py: do not edit
window.LAYERS = {
 "frame": [
  1200,
  1600
 ],
 "made": "silhouette/parts/build_layers.py (StepD by parts)",
 "slots": [
  {
   "id": "sleeve",
   "label": "Sleeves",
   "z": 1
  },
  {
   "id": "neck",
   "label": "Neckline",
   "z": 2
  }
 ],
 "looks": [
  {
   "id": "lehenga",
   "name": "Lehenga choli",
   "note": "Fitted crop top over a high-waisted, flared skirt",
   "base": {
    "file": "assets/layers/lehenga/base-sleeveless.jpg",
    "what": "the lehenga choli without its sleeves (the owner's edit of its photo, tone-matched)"
   },
   "anchors": {
    "neck-l": [
     537.7,
     195.5
    ],
    "neck-r": [
     670.3,
     195.5
    ],
    "cf-neck": [
     602.7,
     223.7
    ],
    "shoulder-l": [
     452.7,
     227.7
    ],
    "shoulder-r": [
     760.7,
     230.4
    ],
    "underarm-l": [
     462.1,
     361.6
    ],
    "underarm-r": [
     742.0,
     338.2
    ],
    "top-hem-l": [
     493.5,
     488.8
    ],
    "top-hem-r": [
     711.2,
     490.8
    ],
    "top-hem-cf": [
     602.7,
     480.8
    ],
    "waist-l": [
     496.9,
     520.3
    ],
    "waist-r": [
     709.8,
     520.3
    ],
    "waist-cf": [
     602.7,
     521.0
    ],
    "hem-l": [
     249.8,
     1325.9
    ],
    "hem-r": [
     956.9,
     1333.9
    ],
    "hem-cf": [
     602.7,
     1405.6
    ],
    "cuff-out-l": [
     334.8,
     737.9
    ],
    "cuff-in-l": [
     409.2,
     755.4
    ],
    "cuff-out-r": [
     870.5,
     735.3
    ],
    "cuff-in-r": [
     792.2,
     752.7
    ]
   },
   "slots": {
    "sleeve": {
     "default": "full",
     "options": [
      {
       "id": "full",
       "name": "Full sleeves",
       "sub": "As photographed",
       "layer": {
        "file": "assets/layers/lehenga/sleeve-full.webp",
        "box": [
         328,
         218,
         551,
         589
        ]
       },
       "kind": "own",
       "joins": [
        "shoulder-l",
        "underarm-l",
        "shoulder-r",
        "underarm-r"
       ],
       "source": "torso-lehenga.png over its sleeveless edit",
       "thumb": "assets/layers/lehenga/thumb-sleeve-full.jpg"
      },
      {
       "id": "short",
       "name": "Short sleeves",
       "sub": "18 cm from the shoulder",
       "layer": {
        "file": "assets/layers/lehenga/sleeve-short.webp",
        "box": [
         340,
         218,
         524,
         322
        ]
       },
       "kind": "own",
       "joins": [
        "shoulder-l",
        "underarm-l",
        "shoulder-r",
        "underarm-r"
       ],
       "source": "the owner's short-sleeve edit of the lehenga photo (made with the mandarin; only its sleeves are used)",
       "thumb": "assets/layers/lehenga/thumb-sleeve-short.jpg"
      },
      {
       "id": "threequarter",
       "name": "Three-quarter",
       "sub": "45 cm from the shoulder",
       "layer": null,
       "kind": "missing",
       "needs": "Its edit: prompt 8, torso-lehenga-sleeve-threequarter.png (prompt 7 with 45 cm)."
      },
      {
       "id": "sleeveless",
       "name": "Sleeveless",
       "sub": "Turned armhole edge",
       "layer": null,
       "kind": "own",
       "joins": [],
       "source": "the base layer itself",
       "thumb": "assets/layers/lehenga/thumb-sleeve-sleeveless.jpg"
      }
     ]
    },
    "neck": {
     "default": "round",
     "options": [
      {
       "id": "round",
       "name": "Round",
       "sub": "As photographed",
       "layer": null,
       "kind": "own",
       "joins": [
        "neck-l",
        "cf-neck",
        "neck-r"
       ],
       "source": "the base layer itself",
       "thumb": "assets/layers/lehenga/thumb-neck-round.jpg"
      },
      {
       "id": "v",
       "name": "V neck",
       "sub": "12 cm deep",
       "layer": {
        "file": "assets/layers/lehenga/neck-v.webp",
        "box": [
         518,
         180,
         177,
         164
        ]
       },
       "kind": "own",
       "joins": [
        "neck-l",
        "cf-neck",
        "neck-r"
       ],
       "source": "the owner's V-neck edit of the lehenga photo",
       "thumb": "assets/layers/lehenga/thumb-neck-v.jpg"
      },
      {
       "id": "boat",
       "name": "Boat neck",
       "sub": "Wide and shallow",
       "layer": {
        "file": "assets/layers/lehenga/neck-boat.webp",
        "box": [
         477,
         187,
         238,
         84
        ]
       },
       "kind": "own",
       "joins": [
        "neck-l",
        "cf-neck",
        "neck-r"
       ],
       "source": "the owner's boat-neck edit of the lehenga photo",
       "thumb": "assets/layers/lehenga/thumb-neck-boat.jpg"
      },
      {
       "id": "mandarin",
       "name": "Mandarin collar",
       "sub": "3 cm stand",
       "layer": {
        "file": "assets/layers/lehenga/neck-mandarin.webp",
        "box": [
         526,
         158,
         153,
         150
        ]
       },
       "kind": "own",
       "joins": [
        "neck-l",
        "cf-neck",
        "neck-r"
       ],
       "source": "the owner's mandarin edit of the lehenga photo",
       "thumb": "assets/layers/lehenga/thumb-neck-mandarin.jpg"
      }
     ]
    }
   },
   "thumb": "assets/layers/lehenga/thumb-look.jpg"
  },
  {
   "id": "anarkali",
   "name": "Anarkali",
   "note": "Fitted bodice, empire seam, flared skirt with a slit",
   "base": {
    "file": "assets/layers/anarkali/base-sleeveless.jpg",
    "what": "the anarkali without its sleeves (the owner's edit of its photo, tone-matched)"
   },
   "anchors": {
    "neck-l": [
     533.7,
     198.2
    ],
    "neck-r": [
     675.0,
     198.2
    ],
    "cf-neck": [
     602.7,
     232.4
    ],
    "shoulder-l": [
     451.3,
     223.7
    ],
    "shoulder-r": [
     754.0,
     223.7
    ],
    "underarm-l": [
     458.7,
     375.0
    ],
    "underarm-r": [
     738.6,
     379.0
    ],
    "waist-l": [
     479.5,
     472.1
    ],
    "waist-r": [
     723.2,
     471.4
    ],
    "waist-cf": [
     602.7,
     476.8
    ],
    "hem-l": [
     350.2,
     1289.1
    ],
    "hem-r": [
     849.1,
     1293.8
    ],
    "hem-cf": [
     602.7,
     1302.5
    ],
    "slit-r": [
     801.6,
     977.7
    ],
    "hem-slit-r": [
     803.6,
     1286.4
    ],
    "cuff-out-l": [
     324.8,
     738.6
    ],
    "cuff-in-l": [
     420.5,
     760.0
    ],
    "cuff-out-r": [
     857.1,
     743.3
    ],
    "cuff-in-r": [
     790.2,
     758.0
    ]
   },
   "slots": {
    "sleeve": {
     "default": "full",
     "options": [
      {
       "id": "full",
       "name": "Full sleeves",
       "sub": "As photographed",
       "layer": {
        "file": "assets/layers/anarkali/sleeve-full.webp",
        "box": [
         318,
         191,
         640,
         616
        ]
       },
       "kind": "own",
       "joins": [
        "shoulder-l",
        "underarm-l",
        "shoulder-r",
        "underarm-r"
       ],
       "source": "torso-anarkali.png over its sleeveless edit",
       "thumb": "assets/layers/anarkali/thumb-sleeve-full.jpg"
      },
      {
       "id": "puff",
       "name": "Puff sleeves",
       "sub": "Gathered, short",
       "layer": {
        "file": "assets/layers/anarkali/sleeve-puff.webp",
        "box": [
         354,
         196,
         497,
         555
        ]
       },
       "kind": "own",
       "joins": [
        "shoulder-l",
        "underarm-l",
        "shoulder-r",
        "underarm-r"
       ],
       "source": "the owner's puff edit of the anarkali photo",
       "thumb": "assets/layers/anarkali/thumb-sleeve-puff.jpg"
      },
      {
       "id": "bell",
       "name": "Bell sleeves",
       "sub": "Placed from the kurta",
       "layer": {
        "file": "assets/layers/anarkali/sleeve-bell.webp",
        "box": [
         286,
         213,
         628,
         513
        ]
       },
       "kind": "placed",
       "joins": [
        "shoulder-l",
        "underarm-l",
        "shoulder-r",
        "underarm-r"
       ],
       "source": "torso-straight-sleeve-bell.png, cut out and placed on the anarkali's anchors",
       "fit": "scale 0.857 / 0.853, rotation within 0.8°, shape kept within 0.8% (limit 5%), shoulder and underarm joins within 0.0 px",
       "thumb": "assets/layers/anarkali/thumb-sleeve-bell.jpg"
      },
      {
       "id": "sleeveless",
       "name": "Sleeveless",
       "sub": "Turned armhole edge",
       "layer": null,
       "kind": "own",
       "joins": [],
       "source": "the base layer itself",
       "thumb": "assets/layers/anarkali/thumb-sleeve-sleeveless.jpg"
      }
     ]
    },
    "neck": {
     "default": "round",
     "options": [
      {
       "id": "round",
       "name": "Round",
       "sub": "As photographed",
       "layer": null,
       "kind": "own",
       "joins": [
        "neck-l",
        "cf-neck",
        "neck-r"
       ],
       "source": "the base layer itself",
       "thumb": "assets/layers/anarkali/thumb-neck-round.jpg"
      },
      {
       "id": "v",
       "name": "V neck",
       "sub": "Ported from the lehenga",
       "layer": {
        "file": "assets/layers/anarkali/neck-v-ported.webp",
        "box": [
         512,
         195,
         190,
         167
        ]
       },
       "kind": "placed",
       "joins": [
        "neck-l",
        "cf-neck",
        "neck-r"
       ],
       "source": "the lehenga's V-neck edit, warped onto this look's measured neckline, its light moved to this photo's",
       "fit": "scale 1.086, rotation 0.1°, on the neckline within 0.0 px (bend 4.4 px), light gain R/G/B 1.007/1.007/1.011",
       "thumb": "assets/layers/anarkali/thumb-neck-v.jpg"
      },
      {
       "id": "mandarin",
       "name": "Mandarin collar",
       "sub": "Placed from the kurta",
       "layer": {
        "file": "assets/layers/anarkali/neck-mandarin.webp",
        "box": [
         529,
         168,
         153,
         262
        ]
       },
       "kind": "placed",
       "joins": [
        "neck-l",
        "cf-neck",
        "neck-r"
       ],
       "source": "torso-straight-part-mandarin.png, cut out and placed on the anarkali's measured neckline",
       "fit": "scale 0.816, rotation 0.6°, on the measured neckline within 6.9 px",
       "thumb": "assets/layers/anarkali/thumb-neck-mandarin.jpg"
      }
     ]
    }
   },
   "thumb": "assets/layers/anarkali/thumb-look.jpg"
  },
  {
   "id": "straight-kurta",
   "name": "Straight kurta",
   "note": "Loose straight kurta with side slits",
   "base": {
    "file": "assets/layers/straight-kurta/base.jpg",
    "what": "the kurta's photo (no sleeveless edit yet)"
   },
   "anchors": {
    "neck-l": [
     510.3,
     253.1
    ],
    "neck-r": [
     690.4,
     251.8
    ],
    "shoulder-l": [
     405.1,
     298.7
    ],
    "shoulder-r": [
     793.5,
     295.3
    ],
    "underarm-l": [
     430.6,
     502.2
    ],
    "underarm-r": [
     771.4,
     472.1
    ],
    "cuff-out-l": [
     274.6,
     898.0
    ],
    "cuff-in-l": [
     383.7,
     922.1
    ],
    "cuff-out-r": [
     926.8,
     897.3
    ],
    "cuff-in-r": [
     818.3,
     920.1
    ],
    "hem-l": [
     389.7,
     1439.7
    ],
    "hem-r": [
     811.6,
     1439.7
    ],
    "slit-l": [
     388.4,
     1329.2
    ],
    "slit-r": [
     812.9,
     1252.2
    ],
    "cf-neck": [
     600.7,
     286.6
    ]
   },
   "slots": {
    "sleeve": {
     "default": "straight",
     "options": [
      {
       "id": "straight",
       "name": "Straight sleeves",
       "sub": "As photographed",
       "layer": null,
       "kind": "own",
       "joins": [
        "shoulder-l",
        "underarm-l",
        "shoulder-r",
        "underarm-r"
       ],
       "source": "the base layer itself",
       "thumb": "assets/layers/straight-kurta/thumb-sleeve-straight.jpg"
      },
      {
       "id": "bell",
       "name": "Bell sleeves",
       "sub": "From the kurta's edit",
       "layer": {
        "file": "assets/layers/straight-kurta/sleeve-bell.webp",
        "box": [
         222,
         256,
         766,
         769
        ]
       },
       "kind": "own",
       "joins": [
        "shoulder-l",
        "underarm-l",
        "shoulder-r",
        "underarm-r"
       ],
       "source": "the owner's bell edit of the kurta photo",
       "thumb": "assets/layers/straight-kurta/thumb-sleeve-bell.jpg"
      },
      {
       "id": "puff",
       "name": "Puff sleeves",
       "sub": "Needs the sleeveless kurta",
       "layer": null,
       "kind": "missing",
       "needs": "The puff sits on the kurta without sleeves: image 1 of StepD §9 (torso-straight-under-sleeveless.png)."
      },
      {
       "id": "sleeveless",
       "name": "Sleeveless",
       "sub": "Needs the sleeveless kurta",
       "layer": null,
       "kind": "missing",
       "needs": "Image 1 of StepD §9 (torso-straight-under-sleeveless.png)."
      }
     ]
    },
    "neck": {
     "default": "round",
     "options": [
      {
       "id": "round",
       "name": "Round",
       "sub": "As photographed",
       "layer": null,
       "kind": "own",
       "joins": [
        "neck-l",
        "cf-neck",
        "neck-r"
       ],
       "source": "the base layer itself",
       "thumb": "assets/layers/straight-kurta/thumb-neck-round.jpg"
      },
      {
       "id": "v",
       "name": "V neck",
       "sub": "Ported from the lehenga",
       "layer": {
        "file": "assets/layers/straight-kurta/neck-v-ported.webp",
        "box": [
         485,
         249,
         237,
         197
        ]
       },
       "kind": "placed",
       "joins": [
        "neck-l",
        "cf-neck",
        "neck-r"
       ],
       "source": "the lehenga's V-neck edit, warped onto this look's measured neckline, its light moved to this photo's",
       "fit": "scale 1.327, rotation -0.4°, on the neckline within 0.0 px (bend 3.6 px), light gain R/G/B 1.073/1.136/1.185",
       "thumb": "assets/layers/straight-kurta/thumb-neck-v.jpg"
      },
      {
       "id": "mandarin",
       "name": "Mandarin collar",
       "sub": "With a front slit",
       "layer": {
        "file": "assets/layers/straight-kurta/neck-mandarin.webp",
        "box": [
         488,
         205,
         214,
         326
        ]
       },
       "kind": "own",
       "joins": [
        "neck-l",
        "cf-neck",
        "neck-r"
       ],
       "source": "the owner's mandarin edit of the kurta photo",
       "thumb": "assets/layers/straight-kurta/thumb-neck-mandarin.jpg"
      },
      {
       "id": "boat",
       "name": "Boat neck",
       "sub": "Wide and shallow",
       "layer": {
        "file": "assets/layers/straight-kurta/neck-boat.webp",
        "box": [
         443,
         161,
         296,
         147
        ]
       },
       "kind": "own",
       "joins": [
        "neck-l",
        "cf-neck",
        "neck-r"
       ],
       "source": "the owner's boat-neck edit of the kurta photo",
       "thumb": "assets/layers/straight-kurta/thumb-neck-boat.jpg"
      }
     ]
    }
   },
   "thumb": "assets/layers/straight-kurta/thumb-look.jpg"
  }
 ]
};
