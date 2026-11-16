window.DEMOS = [
  {
    "id": 1,
    "title": "Release a restriction before a paired visit",
    "description": "A Type 1 pair visits L2, then L3. A Type 2 arrival at L4 releases the temporary L3 restriction.",
    "note": "The actual planner run releases the restriction at step 5, witnesses the paired L2 visit at step 10, and completes the paired L3 visit at step 22.",
    "obligations": [
      "The same two Type 1 robots must visit L2 and then L3 together.",
      "Before release, L3 can contain at most one Type 1 robot.",
      "The release persists after the Type 2 robot leaves L4."
    ],
    "robots": 5,
    "label": "Case 1",
    "meta": "Simulation I · 5 robots · seed 42",
    "video": "demo/generated/case_01.mp4",
    "replay": "demo/generated/case_01.json",
    "validation": "demo/generated/case_01.validation.json",
    "poster": "site/posters/case_01.jpg"
  },
  {
    "id": 2,
    "title": "Repeated visits by the same robot",
    "description": "One selected Type 1 robot visits L2 and then L3, repeatedly.",
    "note": "The video shows the initial prefix and two executions of the closed cycle. The recurrence check evaluates infinite repetition of that cycle.",
    "obligations": [
      "Preserve the selected robot identity across visits.",
      "Visit L2 before the subsequent L3 visit.",
      "Repeat the ordered visits indefinitely."
    ],
    "robots": 5,
    "label": "Case 2",
    "meta": "Simulation I · 5 robots · seed 42",
    "video": "demo/generated/case_02.mp4",
    "replay": "demo/generated/case_02.json",
    "validation": "demo/generated/case_02.validation.json",
    "poster": "site/posters/case_02.jpg"
  },
  {
    "id": 3,
    "title": "A recurring four-region tour",
    "description": "The same Type 1 pair follows an ordered tour through four task regions.",
    "note": "Task cards connect each stage of the selected accepting run to the assigned pair’s positions.",
    "obligations": [
      "Visit L2 → L3 → L4 → L5 in order.",
      "The same two Type 1 robots occupy each region together.",
      "Repeat the tour on a closed cycle."
    ],
    "robots": 5,
    "label": "Case 3",
    "meta": "Simulation II · 5 robots · seed 42",
    "video": "demo/generated/case_03.mp4",
    "replay": "demo/generated/case_03.json",
    "validation": "demo/generated/case_03.validation.json",
    "poster": "site/posters/case_03.jpg"
  },
  {
    "id": 4,
    "title": "Conditional holding and permanent avoidance",
    "description": "A Type 1 pair repeatedly visits L2 and L3, alongside a conditional holding rule and an occupancy limit.",
    "note": "The L5 trigger is unused in this solution. Its unused identity is recorded as a validation witness, not an optimizer assignment.",
    "obligations": [
      "Repeat the same pair’s L2 → L3 visits.",
      "If the separately identified Type 1 robot enters L5, hold it there from the next step until Type 2 reaches L4.",
      "Keep at most one Type 1 robot in L4 at all times."
    ],
    "robots": 5,
    "label": "Case 4",
    "meta": "Simulation II · 5 robots · seed 42",
    "video": "demo/generated/case_04.mp4",
    "replay": "demo/generated/case_04.json",
    "validation": "demo/generated/case_04.validation.json",
    "poster": "site/posters/case_04.jpg"
  },
  {
    "id": 5,
    "title": "Hold until another team arrives",
    "description": "A selected Type 2 robot waits at L4 for a Type 1 pair to reach L3.",
    "note": "The holding condition ties one robot’s permission to leave to another team’s arrival.",
    "obligations": [
      "Reach L4 and, from the next step, hold until two Type 1 robots occupy L3.",
      "The selected Type 2 robot also repeatedly visits L4 and then L3.",
      "Track the same Type 2 identity across these obligations."
    ],
    "robots": 5,
    "label": "Case 5",
    "meta": "Simulation II · 5 robots · seed 42",
    "video": "demo/generated/case_05.mp4",
    "replay": "demo/generated/case_05.json",
    "validation": "demo/generated/case_05.validation.json",
    "poster": "site/posters/case_05.jpg"
  },
  {
    "id": 6,
    "title": "Alternative destinations, limited occupancy",
    "description": "Robots can satisfy recurring visits at either L3 or L5 while obeying permanent L4 limits.",
    "note": "The selected accepting run shows which alternative destination is used at each recorded task event.",
    "obligations": [
      "A selected Type 1 robot repeatedly visits L3 or L5, and repeatedly visits L2.",
      "Two Type 2 robots repeatedly visit L3 or L5 together.",
      "Allow at most one robot of each type in L4."
    ],
    "robots": 5,
    "label": "Case 6",
    "meta": "Simulation II · 5 robots · seed 42",
    "video": "demo/generated/case_06.mp4",
    "replay": "demo/generated/case_06.json",
    "validation": "demo/generated/case_06.validation.json",
    "poster": "site/posters/case_06.jpg"
  },
  {
    "id": 7,
    "title": "Arrival, departure, and a rendezvous",
    "description": "Repeated visits must include departures, and all five robots must meet together once.",
    "note": "Remaining inside a region cannot satisfy an arrival-and-departure obligation.",
    "obligations": [
      "Type 2 repeatedly visits L4, followed by a step with no Type 2 robot there.",
      "Type 1 has the analogous arrival-and-departure rule at L5.",
      "All three Type 1 and both Type 2 robots meet at L3 at least once."
    ],
    "robots": 5,
    "label": "Case 7",
    "meta": "Simulation II · 5 robots · seed 42",
    "video": "demo/generated/case_07.mp4",
    "replay": "demo/generated/case_07.json",
    "validation": "demo/generated/case_07.validation.json",
    "poster": "site/posters/case_07.jpg"
  },
  {
    "id": 8,
    "title": "Unlock two regions before a tour",
    "description": "A joint Type 2 arrival at L4 unlocks L2 and L5 for a recurring tour.",
    "note": "Watch the restriction hatching disappear when the Type 2 pair reaches L4.",
    "obligations": [
      "No Type 2 robot enters L2 or L5 until the selected Type 2 pair first reaches L4.",
      "The same Type 2 pair repeatedly visits L4 → L2 → L5.",
      "Two Type 1 robots repeatedly visit L5 together, or repeatedly visit L3 together."
    ],
    "robots": 5,
    "label": "Case 8",
    "meta": "Simulation II · 5 robots · seed 42",
    "video": "demo/generated/case_08.mp4",
    "replay": "demo/generated/case_08.json",
    "validation": "demo/generated/case_08.validation.json",
    "poster": "site/posters/case_08.jpg"
  },
  {
    "id": 9,
    "title": "Twelve-robot recurring visits",
    "description": "A larger team coordinates full-team and six-robot visits, with a temporary restriction on L4.",
    "note": "Release occurs at step 18; all 12 robots reach L2 at step 41. The six-robot visits to L3 and L4 are witnessed at step 67. The cycle spans steps 67–105.",
    "obligations": [
      "All 12 robots repeatedly occupy L2 together.",
      "At least six robots repeatedly visit L3, and at least six repeatedly visit L4.",
      "Keep L4 empty until L5 and L6 are simultaneously occupied."
    ],
    "robots": 12,
    "label": "Case 9",
    "meta": "Simulation III · 12 robots · seed 42",
    "video": "demo/generated/case_09.mp4",
    "replay": "demo/generated/case_09.json",
    "validation": "demo/generated/case_09.validation.json",
    "poster": "site/posters/case_09.jpg"
  },
  {
    "id": 10,
    "title": "Twelve-robot identity and safety",
    "description": "A fixed six-robot team repeats an ordered visit while smaller groups satisfy other obligations.",
    "note": "The closed cycle spans steps 36–90. The permanent L6 occupancy limit is never released.",
    "obligations": [
      "The same six robots repeatedly visit L2 and then L4 together.",
      "At least three robots repeatedly visit L3; three visit L5 or L6 together at least once.",
      "At most three robots may occupy L6 at any step."
    ],
    "robots": 12,
    "label": "Case 10",
    "meta": "Simulation III · 12 robots · seed 42",
    "video": "demo/generated/case_10.mp4",
    "replay": "demo/generated/case_10.json",
    "validation": "demo/generated/case_10.validation.json",
    "poster": "site/posters/case_10.jpg"
  }
];
