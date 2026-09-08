# Real-photo error report — `2026-09-08_p2-ocr-pp-ocrv5-det960.json`

38 real cases, 141 gold declarations, 49 correct, 92 missed or wrong, 13 spurious.

## Misses by category

| Category | Misses | Share |
|---|---|---|
| 7. The declaration is printed with no label at all (nothing to anchor on) | 19 | 21% |
| 2. OCR read the words but they span several boxes and the extractor did not group them | 19 | 21% |
| 4. OCR read the line with character errors, so the value can never match gold | 18 | 20% |
| 11. The anchor fired and took the wrong neighbouring box as its value | 17 | 18% |
| 1. OCR did not detect the text (under half the gold words are anywhere in the output) | 15 | 16% |
| 6. A wrapped / multi-line value was cut short or over-merged | 3 | 3% |
| 3. The gold sits on one OCR line and no anchor / regex claimed it | 1 | 1% |

## Misses by field and category

| Field | recognition | unlabeled | layout | association | ocr_missed | wrapped | anchor | total |
|---|---|---|---|---|---|---|---|---|
| best_before | 1 | 1 | 3 | 0 | 1 | 1 | 0 | 7 |
| consumer_care | 2 | 1 | 4 | 3 | 1 | 0 | 0 | 11 |
| country_of_origin | 1 | 0 | 4 | 0 | 2 | 0 | 0 | 7 |
| generic_name | 0 | 13 | 0 | 0 | 1 | 0 | 0 | 14 |
| manufacturer | 1 | 0 | 2 | 8 | 2 | 0 | 0 | 13 |
| mfg_date | 1 | 0 | 2 | 1 | 2 | 1 | 0 | 7 |
| mrp | 1 | 2 | 1 | 2 | 3 | 0 | 0 | 9 |
| net_quantity | 8 | 0 | 3 | 2 | 1 | 1 | 1 | 16 |
| unit_sale_price | 3 | 2 | 0 | 1 | 2 | 0 | 0 | 8 |

## Spurious predictions by field

| Field | Count |
|---|---|
| mrp | 4 |
| unit_sale_price | 2 |
| manufacturer | 2 |
| mfg_date | 1 |
| consumer_care | 1 |
| net_quantity | 1 |
| generic_name | 1 |
| best_before | 1 |

## Every miss and spurious prediction

| Case | Field | Gold | Best OCR line (coverage, conf) | Final | Category | Why |
|---|---|---|---|---|---|---|
| ecom_amazon_britannia_tiger | mrp | — | — | M.R.P:10.00 | spurious | predicted a field gold does not have |
| ecom_amazon_britannia_tiger | unit_sale_price | — | — | 29.00/100 g | spurious | predicted a field gold does not have |
| ecom_amazon_figaro_olive_oil | country_of_origin | Country of Origin España | Country of Origin : España (100%, 0.99) | Country of Origin Españia | recognition | prediction is 98% similar to gold: characters OCR misread |
| ecom_amazon_figaro_olive_oil | unit_sale_price | ₹119.80 /100 ml | (119.80 /100 ml) (100%, 0.98) | 2119.80/100 ml | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_g_800g | mfg_date | — | — | Mfg. Date: 21/12/17 | spurious | predicted a field gold does not have |
| ecom_amazon_parle_g_800g | mrp | ₹90 | amazon.in (0%, 0.97) | M.R.P:210.00 | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_g_800g | unit_sale_price | ₹11.25 /100 g | amazon.in (0%, 0.97) | 211.25/100 g | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_krackjack | mrp | ₹128 | amazon.in (0%, 0.99) | M.R.P:2150.00 | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_flipkart_tata_salt | manufacturer | Marketed by: TATA CONSUMER PRODUCTS LIMITED, 1, Bishop Lefroy Road, Kolkata, West Bengal - 700 020. | West Bengal - 700 020. (31%, 0.94) | — | layout | gold words are in the OCR output (62%) but the best single line holds 31% |
| ecom_flipkart_tata_salt | net_quantity | Quantity 1000 g | lodized Salt (1000 g) (50%, 0.99) | NET WT 250G | association | anchor fired but the value came from another box (45% similar) |
| obf_cetaphil_gentle_skin_cleanser_8906 | generic_name | Gentle Skin Cleanser | Gentle (33%, 1.00) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_cetaphil_moisturising_lotion_89060 | best_before | Use Before: 04/26 | Directions for use: (33%, 1.00) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_cetaphil_moisturising_lotion_89060 | generic_name | Moisturising Lotion | Moisturising (50%, 1.00) | Avocado Oil | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_cetaphil_moisturising_lotion_89060 | manufacturer | Marketed by: Galderma India Pvt. Ltd. | Manufactured by: Encube Ethicals Pvt. Ltd. (40%, 0.93) | Manufactured by: Encube Ethicals Pvt. Ltd. Plot No. C1, Madkaim Ind. Estate, Madkaim, Post Mardol | association | anchor fired but the value came from another box (29% similar) |
| obf_cetaphil_moisturising_lotion_89060 | mrp | MRP (Inclusive of all taxes) ₹: 486.00 (Rs. 4.86/ml) | MRP (Inclusive fall taxes) (50%, 0.85) | MRP (Inclusive fall taxes) 486.00 (Rs. 4.86/ml) | recognition | prediction is 99% similar to gold: characters OCR misread |
| obf_himalaya_lip_balm_8901138509231 | generic_name | Lip Balm | Lip (50%, 1.00) | EED OIL | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_himalaya_lip_balm_8901138509231 | net_quantity | Net Wt. 10 g | Net Wt. (100%, 1.00) | Net Wt. 10 | recognition | prediction is 93% similar to gold: characters OCR misread |
| obf_muuchstac_ocean_muuchstac_face_was | best_before | Exp. Dt 04/2027 | Exp. Dt (50%, 0.89) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| obf_muuchstac_ocean_muuchstac_face_was | consumer_care | Customer Care Contact at: Address: Same as above Mob. No./: +91-9892599660 Email Id: customercare@muuchstac.com Website: www.muuchstac.com | Address: (8%, 1.00) | — | layout | gold words are in the OCR output (77%) but the best single line holds 8% |
| obf_muuchstac_ocean_muuchstac_face_was | manufacturer | MARKETED BY: Triology Solutions Pvt. Ltd. CIN: U90009MH2017PTC294630 Address: D3 Kasturi Vandana Complex, Lane Opp Swagat Hotel, Goddev Phathak Road, Bhayandar (E), Maharashtra, India - 401105 | Pvt. Ltd. (9%, 0.99) | — | layout | gold words are in the OCR output (86%) but the best single line holds 9% |
| obf_muuchstac_ocean_muuchstac_face_was | mfg_date | Mfd. 05/2025 | MFD. (50%, 0.98) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| obf_muuchstac_ocean_muuchstac_face_was | mrp | MRP ₹ (Incl. of all taxes) 299.00 | ALL SKIN (20%, 1.00) | MRP 9 | ocr_missed | only 40% of the gold words are anywhere in the OCR output |
| obf_muuchstac_ocean_muuchstac_face_was | net_quantity | Net Vol. 100ml (3.38 FL.OZ) (when packed.) | 100ml (3.38 FL.OZ) (43%, 1.00) | Net Vol. 100ml (3.38 FL.OZ) | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| obf_patanjali_saundarya_aloe_vera_gel_ | generic_name | AYURVEDIC PROPRIETARY MEDICINE | — | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_amul_amul_masti_spiced_buttermilk_ | manufacturer | Marketed by: Gujarat Co-operative Milk Marketing Federation Ltd., Amul Dairy Road, Anand, Gujarat - 388001, India. | Marketed by: Gujarat Co-operative Milk Marketing (43%, 0.98) | Marketed by: Gujarat Co-operative Milk Marketing on a 1 India, Website: www,amul.com | association | anchor fired but the value came from another box (64% similar) |
| off_amul_amul_taaza_amul_taaza_milky_m | generic_name | PASTEURISED HOMOGENISED TONED MILK | TONED MILK (50%, 1.00) | MILKY MILK | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_amul_amul_taaza_amul_taaza_milky_m | net_quantity | Net Content : 500 mL | Net (33%, 1.00) | — | layout | gold words are in the OCR output (100%) but the best single line holds 33% |
| off_balaji_balaji_wafers_chataka_patak | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | INDIAN SNACKS & SAVOURIES (50%, 1.00) | PROPRIETARY FOOD | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_balaji_wafers_chataka_patak | unit_sale_price | UNIT SALE PRICE : ₹ 0.20 PER g | UNIT SALE PRICE: 0.20 PER (100%, 0.93) | UNIT SALE PRICE: 0.20 PER | recognition | prediction is 98% similar to gold: characters OCR misread |
| off_balaji_balaji_wafers_panjabi_tadka | consumer_care | — | — | CONSUMER CARE ECUTIVE +91-7069014141 ON ANY WORKING | spurious | predicted a field gold does not have |
| off_balaji_balaji_wafers_panjabi_tadka | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | INDIAN SNACKS & SAVOURIES (50%, 0.98) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_balaji_wafers_panjabi_tadka | mfg_date | PKD. : 01JUL25 09:02:49 | PKD. : (33%, 0.94) | PKD. : 01JUL25 | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| off_balaji_balaji_wafers_panjabi_tadka | mrp | — | — | MRP INCL. OF ALL TAXES) 1 | spurious | predicted a field gold does not have |
| off_balaji_balaji_wafers_panjabi_tadka | net_quantity | NET WEIGHT : 22g | NET WEIGHT : (67%, 0.96) | NET WEIGHT : 22 | recognition | prediction is 96% similar to gold: characters OCR misread |
| off_balaji_balaji_wafers_panjabi_tadka | unit_sale_price | UNIT SALE PRICE : ₹ 0.23 PER g | UNIT SALE PRICE:0.23 PER (80%, 0.87) | UNIT SALE PRICE:0.23 PER | recognition | prediction is 98% similar to gold: characters OCR misread |
| off_balaji_chataka_pataka_890601050211 | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | INDIAN SNACKS & SAVOURIES (50%, 0.97) | DEHYDRATED VEGETABLE | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_chataka_pataka_890601050211 | mrp | MRP ₹ (*INCL. OF ALL TAXES) : 5.00 | INCL OF AL TAXES) (40%, 0.83) | MRP7 | association | anchor fired but the value came from another box (24% similar) |
| off_balaji_chataka_pataka_890601050211 | unit_sale_price | UNIT SALE PRICE : ₹ 0.20 PER g | UNIT SALE PRICE:020 DED (60%, 0.91) | UNIT SALE PRICE:020 DED | recognition | prediction is 85% similar to gold: characters OCR misread |
| off_bisleri_bisleri_1ltr_made_in_india | best_before | BEST BEFORE SIX MONTHS FROM MANUFACTURE | BEST BEFORE SIX MONTHS FROM MANUFACTURE". (100%, 0.98) | BEST BEFORE SIX MONTHS FROM MANUFACTURE". SORE IN A COL DRY AND VENTILATED PLACE KEE AWAY FROM | wrapped | gold is inside the prediction: neighbouring lines were merged in |
| off_bisleri_bisleri_1ltr_made_in_india | consumer_care | CONTACT: CUSTOMER CARE EXECUTIVE 1800-121-1007 EMAIL: WECARE@BISLERI.CO.IN ADDRESS: SAME AS MKT BY ADDRESS | CONTACT: CUSTOMER CARE EXECUTIVE (36%, 0.96) | CONTACT: CUSTOMER CARE EXECUTIVE EMAIL WECARE@BISLERI.CO.IN DRESS SAME AS MKT Y ARESS TUS @ MMW BISLERI.COM O  IST A WAHARASHTRA-445001. UC NO. 10020022011032 | association | anchor fired but the value came from another box (65% similar) |
| off_bisleri_bisleri_1ltr_made_in_india | generic_name | PACKAGED DRINKING WATER OZONISED | WATER (25%, 1.00) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_bisleri_bisleri_1ltr_made_in_india | manufacturer | MKT BY: BISLERI INTERNATIONAL PVT. LTD., 5TH FLOOR, CTS NO. 525/1A1/A, WESTERN EXPRESS HIGHWAY, ANDHERI (EAST), MUMBAI - 400 099, MAHARASHTRA. | BISLERI INTERNATIONAL PVT. (17%, 0.97) | MFD BY: PRISTINE AQUATICS | association | anchor fired but the value came from another box (20% similar) |
| off_bisleri_bisleri_1ltr_made_in_india | net_quantity | — | — | QUANTITY PER ADDED 100 | spurious | predicted a field gold does not have |
| off_britannia_jimjam_57g_57_8901063029 | generic_name | Flavoured Sandwich Biscuits | Flavoured (33%, 0.95) | Naughty Jam | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_britannia_jimjam_57g_57_8901063029 | net_quantity | BISCUITS NET WEIGHT 57 g | BISCUITS NET WEIGHT (100%, 1.00) | BISCUITS NET WEIGHT 57 | recognition | prediction is 97% similar to gold: characters OCR misread |
| off_britannia_marie_gold_biscuit_89010 | generic_name | BISCUIT | BISCUIT (100%, 1.00) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_britannia_marie_gold_biscuit_89010 | mrp | MRP. ₹10.00 (INCL. OF ALL TAXES) | SCAN 6 GET (0%, 0.98) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_britannia_marie_gold_biscuit_89010 | net_quantity | BISCUITS NET WEIGHT 64 g | BISCUITS NET WEIGHT (100%, 0.97) | BISCUITS NET WEIGHT 649 | recognition | prediction is 95% similar to gold: characters OCR misread |
| off_britannia_marie_gold_biscuit_89010 | unit_sale_price | Rs. 0.16 P.G. | SCAN 6 GET (0%, 0.98) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_bru_bru_instant_coffee_89010305358 | best_before | USE BY 23/01/26 | 24/01/25 23/01/26 RA22 (50%, 0.99) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_bru_bru_instant_coffee_89010305358 | consumer_care | LEVERCARE-QUERY / FEEDBACK, TOLL FREE: 1800-10-22-221, PO BOX 14760, MUMBAI 400 099, LEVER.CARE@UNILEVER.COM | PO BOX 14760, MUMBAI 400099, (27%, 0.96) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_bru_bru_instant_coffee_89010305358 | generic_name | INSTANT COFFEE-CHICORY MIXTURE COFFEE 70% CHICORY 30% | INSTANT COFFEE-CHICORY (80%, 1.00) | INSTANT COFFEE-CHICORY | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_bru_bru_instant_coffee_89010305358 | manufacturer | MKTD. BY: HINDUSTAN UNILEVER LTD. (HUL), UNILEVER HOUSE, CHAKALA, ANDHERI (E), MUMBAI-99. | RIGES (0%, 0.73) | Pkg. Mitrl. Mfd. By: Amcor Puducherry CPCB Regn. No.: PR-05-000-08-AAGCA0510J-22 | ocr_missed | only 30% of the gold words are anywhere in the OCR output |
| off_bru_bru_instant_coffee_89010305358 | mfg_date | PKD. 24/01/25 | 24/01/25 23/01/26 RA22 (50%, 0.99) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_bru_bru_instant_coffee_89010305358 | net_quantity | NET WT.: 1.2 g | NET WT: (50%, 0.95) | NET WT: 001016 | association | anchor fired but the value came from another box (60% similar) |
| off_ching_s_secret_schezwan_chutney_89 | consumer_care | FOR ANY COMPLAINT CONTACT CUSTOMER CARE EXECUTIVE AT MKT BY ADDRESS ABOVE. 18001084488 AND care@tataconsumer.com | FOR ANY COMPLAINT (23%, 0.96) | — | layout | gold words are in the OCR output (92%) but the best single line holds 23% |
| off_ching_s_secret_schezwan_chutney_89 | manufacturer | MKT BY: CAPITAL FOODS PVT. LTD., VILLA CAPITAL, SADHANA COMPOUND, NR. OSHIWARA BRIDGE, S. V. ROAD, JOGESHWARI (W), MUMBAI - 400 102. | MKT BY: CAPITAL FOODS (25%, 0.97) | MKT BY: CAPITAL FOODS VILLA CAPITAL, SADHANA S.V.ROAD, JOGESHWARI FOR ANY COMPLAINT care@tataconsumer.com Mifg by | association | anchor fired but the value came from another box (59% similar) |
| off_ching_secret_dark_soy_sauce_890159 | consumer_care | FOR ANY COMPLAINT CONTACT CONSUMER MANAGER AT BRAND OWNED & MARKETED BY ADDRESS ABOVE. 022-67140100 AND CUSTOMERCARE@CAPITALFOODS.CO.IN | FOR ANY COMPLAI (14%, 0.99) | — | ocr_missed | only 29% of the gold words are anywhere in the OCR output |
| off_ching_secret_dark_soy_sauce_890159 | generic_name | DARK SOY SAUCE (SOYABEAN SAUCE) | Ching' Secret Dark Soy Sauce is the utimate Dei Chinese sct (80%, 0.75) | Natural Colour( | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_ching_secret_dark_soy_sauce_890159 | manufacturer | BRAND OWNED & MARKETED BY: CAPITAL FOODS PVT.LTD., VILLA CAPITAL, SADHANA COMPOUND, NR. OSHIWARA BRIDGE, S.V. ROAD, JOGESHWARI (W), MUMBAI - 400 102. | NNECT AT BRAND (6%, 1.00) | — | ocr_missed | only 24% of the gold words are anywhere in the OCR output |
| off_ching_secret_dark_soy_sauce_890159 | mfg_date | DATE OF MFG.: 10/12/2024 (15:16) | DATE OF MFG.: (50%, 0.95) | DATE OF MFG.: (incl. of all taxes) 10/12/2024(15:16) | association | anchor fired but the value came from another box (77% similar) |
| off_ching_secret_dark_soy_sauce_890159 | mrp | MRP ₹: (incl. of all taxes) 25 (Rs. 0.28/g) | (incl. of all taxes) (60%, 0.93) | MRP7 | association | anchor fired but the value came from another box (21% similar) |
| off_ching_secret_dark_soy_sauce_890159 | unit_sale_price | Rs. 0.28/g | * (0%, 0.29) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_coca_cola_sprite_8901764032707 | country_of_origin | MADE IN INDIA | Sprite (0%, 0.94) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_coca_cola_sprite_8901764032707 | generic_name | — | — | MOMATED WATER | spurious | predicted a field gold does not have |
| off_coca_cola_sprite_8901764032707 | net_quantity | NET QUANTITY: 600 ml | E QUANTITY: (33%, 0.80) | — | layout | gold words are in the OCR output (67%) but the best single line holds 33% |
| off_coca_cola_sprite_sprite_8901764032 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS: SAME AS MFG/MKT BY ADDRESS | CONTACT CONSUMER RESPONSE COORDINATOR AT: (40%, 1.00) | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS: SAME AS MFG/MKT BY ADDRESS RECYCLE | recognition | prediction is 97% similar to gold: characters OCR misread |
| off_coca_cola_sprite_sprite_8901764032 | best_before | — | — | EXPIRY OR BEST BEFORE, OF ALL TAXES): SEE NECK | spurious | predicted a field gold does not have |
| off_coca_cola_sprite_sprite_8901764032 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS : SAME AS MANUFACTURED BY ADDRESS | ADDRESS SAME AS MANUFACTURED BY ADDRESS (40%, 0.97) | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 ADDRESS: SAME AS BATCH NO | association | anchor fired but the value came from another box (72% similar) |
| off_coca_cola_sprite_sprite_8901764032 | country_of_origin | MADE IN INDIA | Sprite (0%, 0.97) | — | layout | gold words are in the OCR output (50%) but the best single line holds 0% |
| off_coca_cola_sprite_sprite_8901764032 | manufacturer | MANUFACTURED BY BENGAL BEVERAGES PVT. LTD., (UNIT-II), DURGAPUR EXPRESSWAY, P.O. DANKUNI COAL COMPLEX, DIST: HOOGHLY - 712 310, WEST BENGAL | COMPLEX, DIST: HOOGHLY - 712 310, WEST BENGAL (47%, 0.97) | MANUFACTURED BY BENGAL BEVERAGES PVT. LTD. (UNIT-I) DURGAPUR EXPRESSWAY, P.O. DANKUNI COAL COMPLEX, DIST: HOOGHLY - 712 310, WEST BENGAL | recognition | prediction is 100% similar to gold: characters OCR misread |
| off_coca_cola_sprite_sprite_8901764032 | mrp | — | — | &MRP 250 | spurious | predicted a field gold does not have |
| off_coca_cola_sprite_sprite_8901764032 | net_quantity | NET QUANTITY: 250 ml | NET QUANTITY: (67%, 0.99) | — | layout | gold words are in the OCR output (100%) but the best single line holds 67% |
| off_coke_diet_coke_can_250ml_890176406 | best_before | BEST BEFORE THREE MONTHS FROM MANUFACTURE WHEN STORED IN A COOL AND DRY PLACE | BEST BEFORE THREE MONTHS FOM MANUFATURE (33%, 0.94) | BEST BEFORE THREE MONTHS FOM MANUFATURE WHEN STOR I A COLD | recognition | prediction is 86% similar to gold: characters OCR misread |
| off_coke_diet_coke_can_250ml_890176406 | manufacturer | — | — | MANUFACTURED BY: PLOT NO. 46O, HSIDC, INDUSTRIAL GROWTH KANDHARI BEVERAGES P CENTER, SAHA-133104 DISTT. AMBALA, H C1800-208-2653 | spurious | predicted a field gold does not have |
| off_coke_diet_coke_can_250ml_890176406 | net_quantity | NET QUANTITY: 300 ml | NET QUANTITY: (67%, 1.00) | NET QUANTITY: 300 | recognition | prediction is 93% similar to gold: characters OCR misread |
| off_haldiram_phalhari_chiwda_890400440 | best_before | USE BY: 23.11.25 | — | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_haldiram_phalhari_chiwda_890400440 | manufacturer | — | — | RVICE MANAGER, ON MARKETED BY ADRESS CALL US AT: 0120-2400286 OR E-MAL SAT STOMERCARE@HALDIRAM.COM IT US AT: WWW.HALDIRAMS.COM rketed By: LDIRAM FOODS INTERNATIONALPVTL t No. 145/146, Old Pardi Naka | spurious | predicted a field gold does not have |
| off_haldiram_phalhari_chiwda_890400440 | mfg_date | MFG. DATE: 24.06.25 | — | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_haldiram_phalhari_chiwda_890400440 | unit_sale_price | — | — | SP:20.25 per g R FEEDBACK OR QUERIES | spurious | predicted a field gold does not have |
| off_hindustan_coca_cola_beverages_pvt_ | country_of_origin | MADE IN INDIA | maza (0%, 0.98) | — | layout | gold words are in the OCR output (50%) but the best single line holds 0% |
| off_kinley_kinley_mineral_water_1ltr_8 | best_before | BEST BEFORE TWELVE MONTHS FROM MANUFACTURE | BEST (17%, 0.86) | — | layout | gold words are in the OCR output (100%) but the best single line holds 17% |
| off_kinley_kinley_mineral_water_1ltr_8 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS : SAME AS MFG BY ADDRESS | ADDRESS 1, GOLF CRS RD, SEC-56, (20%, 0.96) | — | layout | gold words are in the OCR output (100%) but the best single line holds 20% |
| off_kinley_kinley_mineral_water_1ltr_8 | country_of_origin | MADE IN INDIA | SOUTH INDIA (50%, 0.93) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_kinley_kinley_mineral_water_1ltr_8 | manufacturer | MFG BY SOUTH INDIA BOTTLING Co.PVT.LTD., B163-170, SIPCOT INDL. GROWTH CENTRE, NH7, GANGAIKONDAN VILLAGE, TIRUNELVELI DIST., TAMILNADU-627352. | BOTTLING CO.PVT.LTD., B163-170, (19%, 0.92) | MFG BY V SOUTH INDIA SIPCOT TIRUNELVELI MARKETED 303 & 304 | association | anchor fired but the value came from another box (42% similar) |
| off_kissan_mixed_fruit_jam_89010309227 | mrp | — | — | MRP & (INCL. OF ALL TAXES), 67655665 LEVERCARE-QUERY/FEEDBACK PO BOX 14760, MUMBAI 400 099 | spurious | predicted a field gold does not have |
| off_kitkat_nestle_nutrition_kitkat_min | consumer_care | NESTLÉ CONSUMER CARE, P.O. BAG 2, NEW DELHI-110001 WECARE@IN.NESTLE.COM 1800 103 1947 | C1800 103 1947 (20%, 0.89) | NESTLECONSUMERCARE P.O.BAG2, NEW DELH-1001 WECAREIN.NESTLECOM C1800 103 1947 other thannaturall ocurngtransat KNOW YOUR PORTION serve  .9 | association | anchor fired but the value came from another box (70% similar) |
| off_kitkat_nestle_nutrition_kitkat_min | mfg_date | JUL/25 - FEB/26 - 5159045481 | J01V25 - FEB726 - 5159045481 1 2327 (33%, 0.83) | — | ocr_missed | only 33% of the gold words are anywhere in the OCR output |
| off_kitkat_nestle_nutrition_kitkat_min | mrp | ₹ 10/- | C10F (0%, 0.65) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_mazza_the_coca_cola_company_maaza_ | country_of_origin | MADE IN INDIA | india (50%, 0.98) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_mazza_the_coca_cola_company_maaza_ | manufacturer | MFG BY: HINDUSTAN COCA-COLA BEVERAGES PVT LTD, 303&304, BAANI ADDRESS 1, GOLF CRSE, SEC 53, GURUGRAM-122011, HARYANA | MFG BY: HINDUSTAN COCA-COLA BE (21%, 0.96) | MFG BY: HINDUSTAN COCA-COLA BE 303&30 BAANADRE1. GOLF GURUGRAM-122011, HARYANA PLOT NO. 1. BAUSTAE BD | association | anchor fired but the value came from another box (75% similar) |
| off_pepsi_cola_pepsi_8902080104581 | consumer_care | CONTACT CUSTOMER SERVICE MANAGER AT: P.O. BOX 27, DLF QUTAB ENCLAVE-1, GURUGRAM-122002, HARYANA CONSUMER.FEEDBACK@PEPSICO.COM 1800 22 4020 | CONTACT CUSTOMER SERVICE MANAGER (31%, 1.00) | CONTACT CUSTOMER SERVICE MANAGER AT: P.O. BOX 27, DLF QUTAB ENCLAVE-1, GURUGRAM-122002, HARYANA CONSUMER.FEEDBACK@PEPSICO.COM C1800 22 4020 | recognition | prediction is 100% similar to gold: characters OCR misread |
| off_pepsi_cola_pepsi_8902080104581 | manufacturer | MFD. BY: VARUN BEVERAGES LIMITED | MFD. BY: VARUN BEVERAGES UMITED (75%, 1.00) | MKT. BY: PEPSICO INDIA HOLDINGS PVT. LTD | association | anchor fired but the value came from another box (25% similar) |
| off_pepsi_cola_pepsi_8902080104581 | net_quantity | NET QUANTITY 400 ml (250 ml + 150 ml Free) | (250 ml + 150 ml Free*) (50%, 0.93) | NET QUANTITY (250 ml + 150 ml Free*) | recognition | prediction is 91% similar to gold: characters OCR misread |
| off_pepsico_quaker_oats_8901491103794 | mrp | MRP ₹: (INCL. OF ALL TAXES) 79/- | (INCL, OF ALL TAXES) (60%, 0.96) | — | layout | gold words are in the OCR output (80%) but the best single line holds 60% |
| off_pepsico_quaker_oats_8901491103794 | net_quantity | N.QTY: 400 g | N.QTY: (50%, 0.99) | N.QTY: 400 | recognition | prediction is 93% similar to gold: characters OCR misread |
| off_pepsico_quaker_oats_8901491103794 | unit_sale_price | USP ₹ 0.20/- per g | PER SERVE (33%, 0.98) | (USPF0.20/-perg) Umax Packaging Regn. No.: RPCB/RO-Jodh/61 | association | anchor fired but the value came from another box (43% similar) |
| off_tata_tata_salt_8904043901015 | generic_name | Vacuum Evaporated Edible Common Salt | Salt (20%, 0.84) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_tata_tata_salt_8904043901015 | net_quantity | NET QUANTITY: 1 kg | NET (50%, 1.00) | QUANTITY: 1kg | recognition | prediction is 88% similar to gold: characters OCR misread |
| off_thumsup_thums_up_3948764042911 | country_of_origin | MADE IN INDIA | Thyms (0%, 0.80) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_thumsup_thums_up_3948764042911 | net_quantity | NET QUANTITY: 250 ml | Thyms (0%, 0.80) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| phone_reynolds_jetter_classic_ballpen | consumer_care | Consumer Care Officer at the above address. Toll Free No.: 0008 0005 04348 E-mail: reynoldsindiaconsumercare@newellco.com | Toll Free No.: 0008 0005 04348 (38%, 0.98) | — | layout | gold words are in the OCR output (100%) but the best single line holds 38% |
| phone_reynolds_jetter_classic_ballpen | manufacturer | Manufactured, Marketed and Brand Owned by Reynolds Pens India Private Limited, Plot No. C-21, SIPCOT Industrial Park, Irungattukottai, Sriperumbudur, Kanchipuram District, Tamil Nadu - 602 117 | Reynolds Pens India Private (17%, 0.98) | Manufactured, Marketed and Brand Owned by Reynolds Pens India Private Plot No. C-21, Irungattukottai, Sriperumbudur | association | anchor fired but the value came from another box (76% similar) |
| phone_reynolds_jetter_classic_ballpen | mfg_date | Month & Year of Manufacture 02/2026 | Month & Year (50%, 0.99) | Month & Year Manufacture 02/2026 | recognition | prediction is 96% similar to gold: characters OCR misread |
| phone_reynolds_jetter_classic_ballpen | net_quantity | Net Quantity 1 N | Net Quantity (100%, 0.99) | — | anchor | 100% of the gold words sit on one OCR line; nothing claimed it |
