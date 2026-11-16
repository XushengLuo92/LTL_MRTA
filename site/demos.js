window.DEMOS = [
  {
    "id": 1,
    "title": "Mail delivery with a release condition",
    "description": "Two Type 1 robots collect mail together at office L2 and deliver it together to L3. A Type 2 robot visits control room L4 to enable the disinfection process before the pair reaches L3.",
    "obligations": [
      "Use the same Type 1 pair for collection and delivery.",
      "Until Type 2 reaches L4, at most one Type 1 robot may occupy L3. That arrival releases the restriction.",
      "At the paired L2 visit, fewer than two Type 1 robots may be at L3."
    ],
    "robots": 5,
    "label": "Case 1",
    "video": "demo/generated/case_01.mp4",
    "poster": "site/posters/case_01.jpg",
    "paper": "https://arxiv.org/pdf/2101.05694.pdf#page=5"
  },
  {
    "id": 2,
    "title": "Repeated equipment transport",
    "description": "One Type 1 robot repeatedly transports equipment between office L2 and delivery site L3. The paper assumes the disinfection process operates automatically for this task.",
    "obligations": [
      "The same robot must visit L2 and then L3.",
      "Continue making these ordered visits indefinitely. A single round trip is not enough."
    ],
    "robots": 5,
    "label": "Case 2",
    "video": "demo/generated/case_02.mp4",
    "poster": "site/posters/case_02.jpg",
    "paper": "https://arxiv.org/pdf/2101.05694.pdf#page=5"
  },
  {
    "id": 3,
    "title": "A shared four-region patrol",
    "description": "A pair of Type 1 robots makes a recurring tour through L2, L3, L4, and L5, meeting at each region in that order.",
    "obligations": [
      "Keep the same two robots throughout the tour.",
      "Both robots must be in each required region at the same time.",
      "Repeat the complete ordered tour indefinitely."
    ],
    "robots": 5,
    "label": "Case 3",
    "video": "demo/generated/case_03.mp4",
    "poster": "site/posters/case_03.jpg",
    "paper": "https://arxiv.org/pdf/2101.05694.pdf#page=18"
  },
  {
    "id": 4,
    "title": "Repeated delivery with conditional waiting",
    "description": "A Type 1 pair repeatedly visits L2 and then L3. A separately identified Type 1 robot has a waiting obligation whenever it visits L5.",
    "obligations": [
      "The same pair must meet at L2 and then L3 on repeated trips.",
      "After the designated robot visits L5, it must stay there from the next step until a Type 2 robot reaches L4.",
      "L4 may contain at most one Type 1 robot at any time."
    ],
    "robots": 5,
    "label": "Case 4",
    "video": "demo/generated/case_04.mp4",
    "poster": "site/posters/case_04.jpg",
    "paper": "https://arxiv.org/pdf/2101.05694.pdf#page=18"
  },
  {
    "id": 5,
    "title": "Wait for another team to arrive",
    "description": "A Type 2 robot visits L4 and waits for two Type 1 robots to meet at L3. The same Type 2 robot also makes recurring trips from L4 to L3.",
    "obligations": [
      "From the step after the required L4 visit, keep that robot at L4 until the Type 1 pair meets at L3.",
      "Use the same Type 2 robot for the repeated L4 → L3 visits."
    ],
    "robots": 5,
    "label": "Case 5",
    "video": "demo/generated/case_05.mp4",
    "poster": "site/posters/case_05.jpg",
    "paper": "https://arxiv.org/pdf/2101.05694.pdf#page=18"
  },
  {
    "id": 6,
    "title": "Recurring visits with a choice of destination",
    "description": "One Type 1 robot repeatedly visits L2 and also repeatedly visits either L3 or L5. Two Type 2 robots repeatedly meet at either L3 or L5.",
    "obligations": [
      "Use the same Type 1 robot for its L2 visits and its L3-or-L5 visits.",
      "The Type 2 visits require two robots to occupy the chosen region together.",
      "At L4, allow at most one Type 1 robot and at most one Type 2 robot."
    ],
    "robots": 5,
    "label": "Case 6",
    "video": "demo/generated/case_06.mp4",
    "poster": "site/posters/case_06.jpg",
    "paper": "https://arxiv.org/pdf/2101.05694.pdf#page=18"
  },
  {
    "id": 7,
    "title": "Repeated departures and a team rendezvous",
    "description": "Type 2 robots repeatedly visit and leave L4, while Type 1 robots repeatedly visit and leave L5. All five robots must also gather at L3 at least once.",
    "obligations": [
      "Each required Type 2 visit to L4 must eventually be followed by a step with no Type 2 robot there.",
      "Apply the same arrival-and-departure rule to Type 1 at L5.",
      "The rendezvous needs three Type 1 and two Type 2 robots in L3 simultaneously."
    ],
    "robots": 5,
    "label": "Case 7",
    "video": "demo/generated/case_07.mp4",
    "poster": "site/posters/case_07.jpg",
    "paper": "https://arxiv.org/pdf/2101.05694.pdf#page=18"
  },
  {
    "id": 8,
    "title": "Unlock regions before a recurring tour",
    "description": "A Type 2 pair repeatedly tours L4 → L2 → L5. Its first meeting at L4 unlocks L2 and L5 for Type 2 robots.",
    "obligations": [
      "Until that first joint L4 visit, no Type 2 robot may enter L2 or L5.",
      "Use the same Type 2 pair for the recurring ordered tour.",
      "Also require repeated two-robot Type 1 meetings at L5, or repeated two-robot Type 1 meetings at L3."
    ],
    "robots": 5,
    "label": "Case 8",
    "video": "demo/generated/case_08.mp4",
    "poster": "site/posters/case_08.jpg",
    "paper": "https://arxiv.org/pdf/2101.05694.pdf#page=18"
  },
  {
    "id": 9,
    "title": "Full-team and half-team rendezvous",
    "description": "All 12 robots repeatedly meet at L2. Groups of at least six also repeatedly meet at L3 and at L4, subject to an initial restriction on L4.",
    "obligations": [
      "Keep L4 empty until L5 and L6 each contain at least one robot at the same time.",
      "After release, continue the full-team L2 visits and the six-robot L3 and L4 visits indefinitely.",
      "The six-robot groups do not have to preserve fixed robot identities."
    ],
    "robots": 12,
    "label": "Case 9",
    "video": "demo/generated/case_09.mp4",
    "poster": "site/posters/case_09.jpg",
    "paper": "https://arxiv.org/pdf/2101.05694.pdf#page=19"
  },
  {
    "id": 10,
    "title": "A fixed team with a permanent occupancy limit",
    "description": "The same six robots repeatedly meet at L2 and then L4. At least three robots repeatedly meet at L3, and at least three must meet at L5 or L6 once.",
    "obligations": [
      "Preserve the six robot identities across the L2 → L4 visits.",
      "The recurring L3 meetings need at least three robots together.",
      "Never allow more than three robots in L6. This restriction is permanent."
    ],
    "robots": 12,
    "label": "Case 10",
    "video": "demo/generated/case_10.mp4",
    "poster": "site/posters/case_10.jpg",
    "paper": "https://arxiv.org/pdf/2101.05694.pdf#page=20"
  }
];
