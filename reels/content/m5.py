# Module 5 scripts (written so far). Keyed by lesson number inside the module.
from m1 import L, B, C, Q
CH = lambda title, text, pattern="support", source="ideal", level="support": {"kind": "chart", "title": title, "text": text,
     "pattern": pattern, "source": source, "level": level, "query": "abstract blue light"}
MA = lambda title, text, template: {"kind": "math", "title": title, "text": text, "template": template, "query": "abstract light bokeh"}

M5 = {
11: L("Support", "explain", "Ինչո՞ւ է գինը|հետ թռչում|նույն տեղից",
  [B("Support-ը գնային գոտի է, որտեղ գնորդները նախկինում ակտիվ են եղել", "city skyline night"),
   CH("Support", "Գինը մի քանի անգամ հասնում է նույն մակարդակին և հետ թռչում", "support", "ideal"),
   B("Որքան շատ են հպումները, այնքան շատ թրեյդերներ են հետևում այդ մակարդակին", "people walking city"),
   MA("Stop loss և թիրախ", "Շատերը stop loss-ը դնում են support-ի տակ, իսկ թիրախը՝ վերևում", "rr"),
   CH("Իսկ իրականում", "Իրական գրաֆիկում support-ը գոտի է, ոչ թե կատարյալ գիծ", "support", "real", "support"),
   C("Կանոն", "Support-ը կարող է կոտրվել, դրա համար միշտ պետք է stop loss", "calm lake sunrise")],
  "Support՝|գնորդների|գոտի",
  "Support. գոտի, որտեղ գինը հաճախ կանգ է առնում և հետ թռչում։ Ինչպես գտնել այն գրաֆիկում և ինչու է այն կարևոր։",
  "Կարո՞ղ ես գտնել support-ը BTC-ի գրաֆիկում հենց հիմա։",
  ["support", "support level", "սափորթ", "տեխնիկական վերլուծություն", "crypto դաս"],
  ["Support is a price zone where buying interest has repeatedly stopped declines."],
  Q("Ի՞նչ է support-ը", ["Գոտի, որտեղ գնորդները ակտիվ են", "Գոտի, որտեղ վաճառողները ակտիվ են", "Ինդիկատոր"]),
  ["support"], []),
}
