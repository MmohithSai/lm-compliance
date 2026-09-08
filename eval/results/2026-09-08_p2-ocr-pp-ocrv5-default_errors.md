# Real-photo error report — `2026-09-08_p2-ocr-pp-ocrv5-default.json`

38 real cases, 141 gold declarations, 47 correct, 94 missed or wrong, 17 spurious.

## Misses by category

| Category | Misses | Share |
|---|---|---|
| 2. OCR read the words but they span several boxes and the extractor did not group them | 26 | 28% |
| 7. The declaration is printed with no label at all (nothing to anchor on) | 21 | 22% |
| 1. OCR did not detect the text (under half the gold words are anywhere in the output) | 16 | 17% |
| 11. The anchor fired and took the wrong neighbouring box as its value | 15 | 16% |
| 4. OCR read the line with character errors, so the value can never match gold | 11 | 12% |
| 6. A wrapped / multi-line value was cut short or over-merged | 4 | 4% |
| 3. The gold sits on one OCR line and no anchor / regex claimed it | 1 | 1% |

## Misses by field and category

| Field | recognition | unlabeled | association | anchor | layout | ocr_missed | wrapped | total |
|---|---|---|---|---|---|---|---|---|
| best_before | 0 | 1 | 1 | 0 | 5 | 1 | 0 | 8 |
| consumer_care | 3 | 1 | 0 | 0 | 8 | 0 | 0 | 12 |
| country_of_origin | 0 | 0 | 0 | 0 | 5 | 2 | 0 | 7 |
| generic_name | 0 | 14 | 1 | 0 | 0 | 1 | 0 | 16 |
| manufacturer | 1 | 0 | 6 | 0 | 2 | 3 | 1 | 13 |
| mfg_date | 0 | 0 | 2 | 0 | 0 | 3 | 1 | 6 |
| mrp | 1 | 2 | 2 | 0 | 3 | 2 | 1 | 11 |
| net_quantity | 5 | 0 | 1 | 1 | 3 | 2 | 1 | 13 |
| unit_sale_price | 1 | 3 | 2 | 0 | 0 | 2 | 0 | 8 |

## Spurious predictions by field

| Field | Count |
|---|---|
| mrp | 3 |
| best_before | 3 |
| manufacturer | 3 |
| unit_sale_price | 2 |
| consumer_care | 2 |
| net_quantity | 2 |
| mfg_date | 1 |
| generic_name | 1 |

## Every miss and spurious prediction

| Case | Field | Gold | Best OCR line (coverage, conf) | Final | Category | Why |
|---|---|---|---|---|---|---|
| ecom_amazon_britannia_tiger | mrp | — | — | M.R.P: 10.00 | spurious | predicted a field gold does not have |
| ecom_amazon_britannia_tiger | unit_sale_price | — | — | 29.00/100 g | spurious | predicted a field gold does not have |
| ecom_amazon_figaro_olive_oil | mrp | M.R.P: ₹649 | M.R.P.: 7649 (50%, 0.89) | M.R.P.: 7649 | recognition | prediction is 92% similar to gold: characters OCR misread |
| ecom_amazon_figaro_olive_oil | unit_sale_price | ₹119.80 /100 ml | -8%599(119.80 /100 ml) (100%, 0.97) | 2119.80/100 ml | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_g_800g | mfg_date | — | — | Mfg. Date: 21/12/17 | spurious | predicted a field gold does not have |
| ecom_amazon_parle_g_800g | mrp | ₹90 | amazon.in (0%, 0.99) | M.R.P: 10.00 | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_g_800g | unit_sale_price | ₹11.25 /100 g | amazon.in (0%, 0.99) | 211.25/100 g | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_krackjack | mrp | ₹128 | amazon.in (0%, 0.99) | M.R.P:150.00 | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_krackjack | unit_sale_price | ₹18.29 /100 g | (218.29 /100 g) (100%, 0.97) | 218.29 /100 g | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_flipkart_tata_salt | best_before | — | — | BEST BEFORE TWENTY FOUR | spurious | predicted a field gold does not have |
| ecom_flipkart_tata_salt | manufacturer | Marketed by: TATA CONSUMER PRODUCTS LIMITED, 1, Bishop Lefroy Road, Kolkata, West Bengal - 700 020. | Marketed by: TATA CONSUMER PRODUCTS LIMITED, 1, Bishop Letroy Road, Kolkata, (62%, 0.94) | Marketed by: TATA CONSUMER PRODUCTS LIMITED, 1, Bishop Letroy Road, Kolkata | recognition | prediction is 86% similar to gold: characters OCR misread |
| obf_cetaphil_gentle_skin_cleanser_8906 | generic_name | Gentle Skin Cleanser | FOR SENSITIVE SKIN (33%, 1.00) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_cetaphil_moisturising_lotion_89060 | best_before | Use Before: 04/26 | use: (33%, 1.00) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_cetaphil_moisturising_lotion_89060 | generic_name | Moisturising Lotion | Moisturising (50%, 1.00) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_cetaphil_moisturising_lotion_89060 | manufacturer | Marketed by: Galderma India Pvt. Ltd. | Marketed by: Galderma Inda Pvt. Ltd. (80%, 0.90) | Marketed by: Galderma Inda Pvt. Ltd. 8th floor, D Wing, Unit 8o1 & 802, 6 Wing 2 Lotu Corporat ark O Wsten Express Highway, Goregaon East Mumbai, 400063, Maharashtra, India. For consumerp or contact +51 22 4033n818 or emal at info.india@galderma.com | association | anchor fired but the value came from another box (25% similar) |
| obf_himalaya_lip_balm_8901138509231 | generic_name | Lip Balm | Lip (50%, 1.00) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_himalaya_lip_balm_8901138509231 | net_quantity | Net Wt. 10 g | Net (100%, 1.00) | — | anchor | 100% of the gold words sit on one OCR line; nothing claimed it |
| obf_muuchstac_ocean_muuchstac_face_was | best_before | Exp. Dt 04/2027 | Exp. (50%, 0.99) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| obf_muuchstac_ocean_muuchstac_face_was | consumer_care | Customer Care Contact at: Address: Same as above Mob. No./: +91-9892599660 Email Id: customercare@muuchstac.com Website: www.muuchstac.com | Address: (8%, 0.99) | — | layout | gold words are in the OCR output (92%) but the best single line holds 8% |
| obf_muuchstac_ocean_muuchstac_face_was | country_of_origin | MADE IN INDIA | India (50%, 1.00) | — | layout | gold words are in the OCR output (100%) but the best single line holds 50% |
| obf_muuchstac_ocean_muuchstac_face_was | generic_name | FACE WASH | FACE (50%, 1.00) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_muuchstac_ocean_muuchstac_face_was | manufacturer | MARKETED BY: Triology Solutions Pvt. Ltd. CIN: U90009MH2017PTC294630 Address: D3 Kasturi Vandana Complex, Lane Opp Swagat Hotel, Goddev Phathak Road, Bhayandar (E), Maharashtra, India - 401105 | Solutions (5%, 1.00) | — | layout | gold words are in the OCR output (91%) but the best single line holds 5% |
| obf_muuchstac_ocean_muuchstac_face_was | mfg_date | Mfd. 05/2025 | MFD. (50%, 1.00) | Mfd. y \| 22 June 202557003mF | association | anchor fired but the value came from another box (45% similar) |
| obf_muuchstac_ocean_muuchstac_face_was | mrp | MRP ₹ (Incl. of all taxes) 299.00 | ALL SKIN (20%, 1.00) | MRP 2027 | ocr_missed | only 40% of the gold words are anywhere in the OCR output |
| obf_muuchstac_ocean_muuchstac_face_was | net_quantity | Net Vol. 100ml (3.38 FL.OZ) (when packed.) | 100ml (3.38 FL.OZ) (43%, 0.99) | Net Vol. 100ml (3.38 FL.OZ) | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| obf_patanjali_saundarya_aloe_vera_gel_ | generic_name | AYURVEDIC PROPRIETARY MEDICINE | — | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_amul_amul_masti_spiced_buttermilk_ | manufacturer | Marketed by: Gujarat Co-operative Milk Marketing Federation Ltd., Amul Dairy Road, Anand, Gujarat - 388001, India. | Gujarat - 388001, (21%, 0.94) | Marketed by: Gujarat Federation India, Website | association | anchor fired but the value came from another box (49% similar) |
| off_amul_amul_taaza_amul_taaza_milky_m | generic_name | PASTEURISED HOMOGENISED TONED MILK | TONED MILK (50%, 1.00) | TONED MILK | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_balaji_wafers_chataka_patak | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | INDIAN SNACKS & SAVOURIES (50%, 1.00) | PROPRIETARY FOOD | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_balaji_wafers_chataka_patak | mrp | MRP ₹ (#INCL. OF ALL TAXES) : 5.00 | (INCL. OF ALL TAXES) (60%, 0.94) | MRP7 | association | anchor fired but the value came from another box (24% similar) |
| off_balaji_balaji_wafers_chataka_patak | net_quantity | NET WEIGHT : 25g | NET (33%, 1.00) | — | layout | gold words are in the OCR output (100%) but the best single line holds 33% |
| off_balaji_balaji_wafers_panjabi_tadka | consumer_care | — | — | CONSUMER CARE YECUTIVE +91-7069014141 ON ANY WORKING | spurious | predicted a field gold does not have |
| off_balaji_balaji_wafers_panjabi_tadka | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | INDIAN SNACKS & SAVOURIES (50%, 0.96) | PROPRIETARY FOOD | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_balaji_wafers_panjabi_tadka | mfg_date | PKD. : 01JUL25 09:02:49 | PKD. : (33%, 0.99) | PKD. : 01JUL25 | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| off_balaji_balaji_wafers_panjabi_tadka | net_quantity | NET WEIGHT : 22g | NET WEIGHT : (67%, 0.96) | NET WEIGHT : 221 | recognition | prediction is 92% similar to gold: characters OCR misread |
| off_balaji_balaji_wafers_panjabi_tadka | unit_sale_price | UNIT SALE PRICE : ₹ 0.23 PER g | UNIT SALE PRICE: 0.23 PER (100%, 0.97) | UNIT SALE PRICE: 0.23 PER | recognition | prediction is 98% similar to gold: characters OCR misread |
| off_balaji_chataka_pataka_890601050211 | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | PROPRIETARY FOOD (33%, 1.00) | DEHYDRATED VEGETABLE | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_chataka_pataka_890601050211 | mrp | MRP ₹ (*INCL. OF ALL TAXES) : 5.00 | (INCL OF LL TAXES) (40%, 0.88) | — | layout | gold words are in the OCR output (100%) but the best single line holds 40% |
| off_balaji_chataka_pataka_890601050211 | unit_sale_price | UNIT SALE PRICE : ₹ 0.20 PER g | UNIT SALE PRICE:3 020 DED (60%, 0.92) | UNIT SALE PRICE:3 020 DED | association | anchor fired but the value came from another box (83% similar) |
| off_bisleri_bisleri_1ltr_made_in_india | best_before | BEST BEFORE SIX MONTHS FROM MANUFACTURE | FROM (17%, 1.00) | — | layout | gold words are in the OCR output (83%) but the best single line holds 17% |
| off_bisleri_bisleri_1ltr_made_in_india | consumer_care | CONTACT: CUSTOMER CARE EXECUTIVE 1800-121-1007 EMAIL: WECARE@BISLERI.CO.IN ADDRESS: SAME AS MKT BY ADDRESS | ADDRESS: (18%, 0.98) | — | layout | gold words are in the OCR output (100%) but the best single line holds 18% |
| off_bisleri_bisleri_1ltr_made_in_india | generic_name | PACKAGED DRINKING WATER OZONISED | WATER (25%, 1.00) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_bisleri_bisleri_1ltr_made_in_india | manufacturer | MKT BY: BISLERI INTERNATIONAL PVT. LTD., 5TH FLOOR, CTS NO. 525/1A1/A, WESTERN EXPRESS HIGHWAY, ANDHERI (EAST), MUMBAI - 400 099, MAHARASHTRA. | MUMBAI - 400 099, MAHARASHTRA. (22%, 0.95) | MFD BY: PRISTINE PLOT NO. -15S, MIDC LOHARA, MAHARASHTRA-445001. UC NO. 10020022011032 | association | anchor fired but the value came from another box (31% similar) |
| off_bisleri_bisleri_1ltr_made_in_india | net_quantity | — | — | QUANTITY "ADDED 100 | spurious | predicted a field gold does not have |
| off_britannia_jimjam_57g_57_8901063029 | generic_name | Flavoured Sandwich Biscuits | Sandwich Biscuits (67%, 0.99) | Naughty Jam | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_britannia_marie_gold_biscuit_89010 | generic_name | BISCUIT | BISCUIT (100%, 1.00) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_britannia_marie_gold_biscuit_89010 | mrp | MRP. ₹10.00 (INCL. OF ALL TAXES) | 210 (0%, 0.52) | — | layout | gold words are in the OCR output (60%) but the best single line holds 0% |
| off_britannia_marie_gold_biscuit_89010 | unit_sale_price | Rs. 0.16 P.G. | 210 (0%, 0.52) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_bru_bru_instant_coffee_89010305358 | best_before | USE BY 23/01/26 | RIGSAROMA (0%, 0.94) | — | layout | gold words are in the OCR output (50%) but the best single line holds 0% |
| off_bru_bru_instant_coffee_89010305358 | consumer_care | LEVERCARE-QUERY / FEEDBACK, TOLL FREE: 1800-10-22-221, PO BOX 14760, MUMBAI 400 099, LEVER.CARE@UNILEVER.COM | PO B0X 14760, MUMBAI 400 099 (36%, 0.92) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_bru_bru_instant_coffee_89010305358 | generic_name | INSTANT COFFEE-CHICORY MIXTURE COFFEE 70% CHICORY 30% | INSTANT COFFEE-CHICORY (80%, 1.00) | INSTANT COFFEE-CHICORY | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_bru_bru_instant_coffee_89010305358 | manufacturer | MKTD. BY: HINDUSTAN UNILEVER LTD. (HUL), UNILEVER HOUSE, CHAKALA, ANDHERI (E), MUMBAI-99. | MKTD. BY: HINDUSTAN UNILEVER LTD. (50%, 0.98) | MKTD. BY: HINDUSTAN UNILEVER LTD. (HUL),UNILEVER HOUSE, CHAKALA ANDHERI (E), MUMBAI-99. FOR MFR. & MPG. READ IST CHARACTER OF BATCH AND SEB BELOW. MPG. BY: (A) ABISHEK (R) ROHINI PACKER, FSSAILIC.NO. 10012042000164.STORE INA | wrapped | gold is inside the prediction: neighbouring lines were merged in |
| off_bru_bru_instant_coffee_89010305358 | mfg_date | PKD. 24/01/25 | RIGSAROMA (0%, 0.94) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_bru_bru_instant_coffee_89010305358 | net_quantity | NET WT.: 1.2 g | NET WT.: (50%, 0.94) | NET WT.: 1.28 | recognition | prediction is 89% similar to gold: characters OCR misread |
| off_ching_s_secret_schezwan_chutney_89 | consumer_care | FOR ANY COMPLAINT CONTACT CUSTOMER CARE EXECUTIVE AT MKT BY ADDRESS ABOVE. 18001084488 AND care@tataconsumer.com | No and see above. (15%, 0.95) | — | layout | gold words are in the OCR output (92%) but the best single line holds 15% |
| off_ching_s_secret_schezwan_chutney_89 | manufacturer | MKT BY: CAPITAL FOODS PVT. LTD., VILLA CAPITAL, SADHANA COMPOUND, NR. OSHIWARA BRIDGE, S. V. ROAD, JOGESHWARI (W), MUMBAI - 400 102. | BY: CAPITAL (12%, 0.99) | Mfg by: (A) Lic. (C) Lic No: (P) Lic. No | association | anchor fired but the value came from another box (12% similar) |
| off_ching_secret_dark_soy_sauce_890159 | consumer_care | FOR ANY COMPLAINT CONTACT CONSUMER MANAGER AT BRAND OWNED & MARKETED BY ADDRESS ABOVE. 022-67140100 AND CUSTOMERCARE@CAPITALFOODS.CO.IN | FOR ANY (14%, 0.91) | — | layout | gold words are in the OCR output (50%) but the best single line holds 14% |
| off_ching_secret_dark_soy_sauce_890159 | generic_name | DARK SOY SAUCE (SOYABEAN SAUCE) | SAUCE (40%, 1.00) | Natural Colour | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_ching_secret_dark_soy_sauce_890159 | manufacturer | BRAND OWNED & MARKETED BY: CAPITAL FOODS PVT.LTD., VILLA CAPITAL, SADHANA COMPOUND, NR. OSHIWARA BRIDGE, S.V. ROAD, JOGESHWARI (W), MUMBAI - 400 102. | () Pan Foods (Div. of Kayem (6%, 0.94) | Manufactured by: (A) Vrinda Aagro, () Pan Foods (Div. of Kayem Lic. No.10012064000055 (N) ANN Distt | ocr_missed | only 18% of the gold words are anywhere in the OCR output |
| off_ching_secret_dark_soy_sauce_890159 | mfg_date | DATE OF MFG.: 10/12/2024 (15:16) | DATE OF MFG.: (50%, 0.97) | DATE OF MFG.: (incl. of all taxes) 10/12/2024(15:16) | association | anchor fired but the value came from another box (77% similar) |
| off_ching_secret_dark_soy_sauce_890159 | mrp | MRP ₹: (incl. of all taxes) 25 (Rs. 0.28/g) | (incl. of all taxes) (60%, 0.95) | MRP3: 25(Rs.0.28/9) | association | anchor fired but the value came from another box (54% similar) |
| off_ching_secret_dark_soy_sauce_890159 | unit_sale_price | Rs. 0.28/g | @ (0%, 0.35) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_coca_cola_sprite_8901764032707 | country_of_origin | MADE IN INDIA | Sprite (0%, 0.99) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_coca_cola_sprite_8901764032707 | generic_name | — | — | MOOMATED WATER | spurious | predicted a field gold does not have |
| off_coca_cola_sprite_8901764032707 | net_quantity | NET QUANTITY: 600 ml | 600 ml (33%, 0.98) | — | ocr_missed | only 33% of the gold words are anywhere in the OCR output |
| off_coca_cola_sprite_sprite_8901764032 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS: SAME AS MFG/MKT BY ADDRESS | CONTACT CONSUMER RESPONSE COORDINATOR AT: (40%, 1.00) | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS: SAME AS MFG/MKT BY ADDRESS RECYCLE | recognition | prediction is 97% similar to gold: characters OCR misread |
| off_coca_cola_sprite_sprite_8901764032 | net_quantity | — | — | NET QUANTITY: 2.20 L | spurious | predicted a field gold does not have |
| off_coca_cola_sprite_sprite_8901764032 | best_before | — | — | OR BEST BEFORE, SEE TAXES): ENECK | spurious | predicted a field gold does not have |
| off_coca_cola_sprite_sprite_8901764032 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS : SAME AS MANUFACTURED BY ADDRESS | ADDRESS SAME AS MANUFACTURED BY ADDRESS (40%, 0.95) | — | layout | gold words are in the OCR output (100%) but the best single line holds 40% |
| off_coca_cola_sprite_sprite_8901764032 | country_of_origin | MADE IN INDIA | Sprite (0%, 0.91) | — | layout | gold words are in the OCR output (50%) but the best single line holds 0% |
| off_coca_cola_sprite_sprite_8901764032 | manufacturer | MANUFACTURED BY BENGAL BEVERAGES PVT. LTD., (UNIT-II), DURGAPUR EXPRESSWAY, P.O. DANKUNI COAL COMPLEX, DIST: HOOGHLY - 712 310, WEST BENGAL | DIST: HOOGHLY - 712 310, WEST BENGAL (41%, 0.96) | MANUFACTURED BY 186LE (UNIT-M), DURGAPUR EPITER COMPLEX, DIST: HOOGHLY fssal MIOIOA ARDA | association | anchor fired but the value came from another box (58% similar) |
| off_coca_cola_sprite_sprite_8901764032 | mrp | — | — | BATCH NO. & MRP 250 | spurious | predicted a field gold does not have |
| off_coca_cola_sprite_sprite_8901764032 | net_quantity | NET QUANTITY: 250 ml | NET QUANTITY: (67%, 1.00) | — | layout | gold words are in the OCR output (100%) but the best single line holds 67% |
| off_coke_diet_coke_can_250ml_890176406 | best_before | BEST BEFORE THREE MONTHS FROM MANUFACTURE WHEN STORED IN A COOL AND DRY PLACE | E THREE MONTHS FROM MANUFACTURE (33%, 0.94) | "BEST BEFORE TRADEMARK | association | anchor fired but the value came from another box (36% similar) |
| off_coke_diet_coke_can_250ml_890176406 | consumer_care | — | — | CONTACT CONSUMER RESPONSE COORDN C1800-208-2653 ADDRESS: SAME AS MANUFACTURED B | spurious | predicted a field gold does not have |
| off_coke_diet_coke_can_250ml_890176406 | net_quantity | NET QUANTITY: 300 ml | NET QUANTITY: (67%, 1.00) | NET QUANTITY: 300 | recognition | prediction is 93% similar to gold: characters OCR misread |
| off_haldiram_phalhari_chiwda_890400440 | best_before | USE BY: 23.11.25 | — | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_haldiram_phalhari_chiwda_890400440 | mfg_date | MFG. DATE: 24.06.25 | — | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_haldiram_phalhari_chiwda_890400440 | unit_sale_price | — | — | SP: { 0.25 per g FEEDBACK OR | spurious | predicted a field gold does not have |
| off_hindustan_coca_cola_beverages_pvt_ | country_of_origin | MADE IN INDIA | indiahelpline@coca-cola.com (50%, 0.94) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_hindustan_coca_cola_beverages_pvt_ | manufacturer | — | — | EUS MFG BY ADORES EXIBATCH INCL OF LL TXES: SE EK DR PA AWAY FROM DIRECT SUNLIGHT. NEA FOR SEAL IS BROKEN. IE.FROPENING. LEER SMALL DARK PARTICLES | spurious | predicted a field gold does not have |
| off_kinley_kinley_mineral_water_1ltr_8 | best_before | BEST BEFORE TWELVE MONTHS FROM MANUFACTURE | BEFORE TWELVE MONTHS (50%, 0.95) | — | layout | gold words are in the OCR output (100%) but the best single line holds 50% |
| off_kinley_kinley_mineral_water_1ltr_8 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS : SAME AS MFG BY ADDRESS | CONTACT CONSUMER (20%, 0.98) | — | layout | gold words are in the OCR output (80%) but the best single line holds 20% |
| off_kinley_kinley_mineral_water_1ltr_8 | country_of_origin | MADE IN INDIA | nley (0%, 0.90) | — | layout | gold words are in the OCR output (50%) but the best single line holds 0% |
| off_kinley_kinley_mineral_water_1ltr_8 | manufacturer | MFG BY SOUTH INDIA BOTTLING Co.PVT.LTD., B163-170, SIPCOT INDL. GROWTH CENTRE, NH7, GANGAIKONDAN VILLAGE, TIRUNELVELI DIST., TAMILNADU-627352. | OTH CENTRE, NH7, GANGAIKONDAN VILLAGE (25%, 0.93) | — | ocr_missed | only 38% of the gold words are anywhere in the OCR output |
| off_kissan_mixed_fruit_jam_89010309227 | best_before | — | — | PKD., USE BY & BATCH 1800-10-20 | spurious | predicted a field gold does not have |
| off_kissan_mixed_fruit_jam_89010309227 | manufacturer | — | — | MFG. BY: FARMS POST HARVEST CARE LIMITED (A) | spurious | predicted a field gold does not have |
| off_kissan_mixed_fruit_jam_89010309227 | mrp | — | — | MRP & (INCL. OF ALL 57657229 LEVERCARE-QUERY 400 | spurious | predicted a field gold does not have |
| off_kissan_mixed_fruit_jam_89010309227 | net_quantity | NET WEIGHT: 90 g | NET (50%, 1.00) | — | layout | gold words are in the OCR output (100%) but the best single line holds 50% |
| off_kitkat_nestle_nutrition_kitkat_min | consumer_care | NESTLÉ CONSUMER CARE, P.O. BAG 2, NEW DELHI-110001 WECARE@IN.NESTLE.COM 1800 103 1947 | 1800 103 1947 (30%, 0.95) | NESTLECONSUMERCARE Nestle P.O.BAG2, NEW DELH-1001 WECARE@IN.NESTLECOM 1800 103 1947 | recognition | prediction is 94% similar to gold: characters OCR misread |
| off_kitkat_nestle_nutrition_kitkat_min | mfg_date | JUL/25 - FEB/26 - 5159045481 | 25 -FEB726 -5159045481 1 2327 (33%, 0.92) | — | ocr_missed | only 33% of the gold words are anywhere in the OCR output |
| off_kitkat_nestle_nutrition_kitkat_min | mrp | ₹ 10/- | 10F (0%, 0.80) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_kurkure_pepsico_kurkure_masala_mun | consumer_care | THE CONSUMER SERVICES MANAGER, PEPSICO INDIA HOLDINGS PVT. LTD., P.O. BOX-27, DLF QUTAB ENCLAVE, PHASE-1, GURUGRAM - 122002, HARYANA, INDIA. OR CALL US AT 1800 22 4020 OR EMAIL US AT CONSUMER.FEEDBACK@PEPSICO.COM | PepsiCo India Holdings Pvt. Ltd. (26%, 0.99) | — | layout | gold words are in the OCR output (100%) but the best single line holds 26% |
| off_kurkure_pepsico_kurkure_masala_mun | mrp | MRP Rs. 10.00 (INCL. OF ALL TAXES) | (INCL. OF ALL TAXES) (60%, 0.98) | $MRP 10.00 | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| off_mazza_the_coca_cola_company_maaza_ | country_of_origin | MADE IN INDIA | india (50%, 0.99) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_mazza_the_coca_cola_company_maaza_ | manufacturer | MFG BY: HINDUSTAN COCA-COLA BEVERAGES PVT LTD, 303&304, BAANI ADDRESS 1, GOLF CRSE, SEC 53, GURUGRAM-122011, HARYANA | 303&304, BAANI (14%, 0.95) | — | ocr_missed | only 36% of the gold words are anywhere in the OCR output |
| off_pepsi_cola_pepsi_8902080104581 | consumer_care | CONTACT CUSTOMER SERVICE MANAGER AT: P.O. BOX 27, DLF QUTAB ENCLAVE-1, GURUGRAM-122002, HARYANA CONSUMER.FEEDBACK@PEPSICO.COM 1800 22 4020 | CONTACT CUSTOMER SERVICE MANAGER (31%, 0.99) | CONTACT CUSTOMER SERVICE MANAGER AT: P.O. BOX 27, DLF QUTAB ENCLAVE-1, GURUGRAM-122002, HARYANA CONSUMER.FEEDBACK@PEPSICO.COM C1800 22 4020 | recognition | prediction is 100% similar to gold: characters OCR misread |
| off_pepsi_cola_pepsi_8902080104581 | manufacturer | MFD. BY: VARUN BEVERAGES LIMITED | MFD. BY: VARUN BEVERAGES UIMITED (75%, 0.95) | MKT. BY: PEPSICO INDIA HOLDINGS PVT. LTD | association | anchor fired but the value came from another box (25% similar) |
| off_pepsi_cola_pepsi_8902080104581 | net_quantity | NET QUANTITY 400 ml (250 ml + 150 ml Free) | (250 ml + 150 ml Free*) (50%, 0.93) | NET QUANTITY (250 ml + 150 ml Free*) | recognition | prediction is 91% similar to gold: characters OCR misread |
| off_pepsico_quaker_oats_8901491103794 | best_before | USE BY: 05 SEP 24 | 06 SEP 23 (50%, 0.98) | — | layout | gold words are in the OCR output (100%) but the best single line holds 50% |
| off_pepsico_quaker_oats_8901491103794 | manufacturer | — | — | MKT. BY: PEPSICO | spurious | predicted a field gold does not have |
| off_pepsico_quaker_oats_8901491103794 | mrp | MRP ₹: (INCL. OF ALL TAXES) 79/- | 79/- (20%, 0.85) | — | layout | gold words are in the OCR output (100%) but the best single line holds 20% |
| off_pepsico_quaker_oats_8901491103794 | unit_sale_price | USP ₹ 0.20/- per g | Per Serve (40 g) (33%, 0.90) | (USP70.20/-perg) Regn. No.: RPCB/RO-Jodh/61 | association | anchor fired but the value came from another box (54% similar) |
| off_tata_tata_salt_8904043901015 | generic_name | Vacuum Evaporated Edible Common Salt | Salt (20%, 0.90) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_tata_tata_salt_8904043901015 | net_quantity | NET QUANTITY: 1 kg | NET (50%, 1.00) | QUANTITY: 1kg | recognition | prediction is 88% similar to gold: characters OCR misread |
| off_thumsup_thums_up_3948764042911 | country_of_origin | MADE IN INDIA | c0m (0%, 0.51) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_thumsup_thums_up_3948764042911 | net_quantity | NET QUANTITY: 250 ml | c0m (0%, 0.51) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| phone_reynolds_jetter_classic_ballpen | consumer_care | Consumer Care Officer at the above address. Toll Free No.: 0008 0005 04348 E-mail: reynoldsindiaconsumercare@newellco.com | Consumer (8%, 1.00) | — | layout | gold words are in the OCR output (100%) but the best single line holds 8% |
| phone_reynolds_jetter_classic_ballpen | generic_name | Generic Name Ball Pen | Generic (25%, 0.97) | Available Ink Colour | association | anchor fired but the value came from another box (17% similar) |
| phone_reynolds_jetter_classic_ballpen | manufacturer | Manufactured, Marketed and Brand Owned by Reynolds Pens India Private Limited, Plot No. C-21, SIPCOT Industrial Park, Irungattukottai, Sriperumbudur, Kanchipuram District, Tamil Nadu - 602 117 | Marketed and (9%, 0.97) | — | layout | gold words are in the OCR output (100%) but the best single line holds 9% |
| phone_reynolds_jetter_classic_ballpen | net_quantity | Net Quantity 1 N | Net (50%, 1.00) | Quantity Net 1N | association | anchor fired but the value came from another box (77% similar) |
