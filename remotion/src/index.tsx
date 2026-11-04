// Compositions. Analysis = daily analysis Reel (see Analysis.tsx); Short = short lesson Reel (see Short.tsx).
// All numbers come from props.json written by the Python pipeline from real data; demos below are placeholders only.
import React from "react";
import {Short, ShortProps, timeline} from "./Short";
import {Analysis, Props, ANALYSIS_FRAMES} from "./Analysis";
import {registerRoot, Composition, getInputProps} from "remotion";

const DEMO: Props = {
  symbol: "BTCUSD", tf: "4H", asset: "BTC", date: "03.11", subtitle: "ՕՐՎԱ ՎԵՐԼՈՒԾՈՒԹՅՈՒՆ",
  candles: [{o: 1, h: 2, l: 0.5, c: 1.5}, {o: 1.5, h: 2.2, l: 1, c: 1.2}], start: 0,
  zone: [0.5, 0.7], zoneKind: "S", touches: [0], other: 2.2, fib: {}, last: 1.2,
  head: "Demo", headAccent: "", scenarios: [], fmt: {other: "2.2", zone: "0.5", last: "1.2"},
};

const SHORT_DEMO: ShortProps = {
  index: "07", series: "ՌԻՍԿ ԱՌԱՆՑ ՁԱՆՁՐՈՒՅԹԻ", tag: "ՕՐԻՆԱԿ", hero: "coins2", theme: "ti",
  hook: "10 գործարքից 7-ը շահույթով է, իսկ հաշիվը՝ *մինուսում*։",
  beats: [{big: "+7", text: "7 × (+1)"}, {big: "−12", text: "3 × (−4)", loss: true}, {big: "−5", text: "+7 − 12", loss: true}],
  rule: "Կարևորը ոչ թե «որքան հաճախ», այլ _«որքան»_ է։",
};
const shortProps = {...SHORT_DEMO, ...(getInputProps() as Partial<ShortProps>)} as ShortProps;

registerRoot(() => (<>
  <Composition id="Short" component={Short as any} fps={30} width={1080} height={1920}
    durationInFrames={timeline(shortProps).total} defaultProps={shortProps} />
  <Composition id="Analysis" component={Analysis as any} durationInFrames={ANALYSIS_FRAMES} fps={30} width={1080} height={1920}
    defaultProps={{...DEMO, ...(getInputProps() as Partial<Props>)}} />
</>));
