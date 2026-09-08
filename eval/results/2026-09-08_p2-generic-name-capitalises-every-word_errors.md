# Real-photo error report — `2026-09-08_p2-generic-name-capitalises-every-word.json`

38 real cases, 141 gold declarations, 71 correct, 70 missed or wrong, 7 spurious.

## Misses by category

| Category | Misses | Share |
|---|---|---|
| 1. OCR did not detect the text (under half the gold words are anywhere in the output) | 23 | 33% |
| 2. OCR read the words but they span several boxes and the extractor did not group them | 15 | 21% |
| 7. The declaration is printed with no label at all (nothing to anchor on) | 12 | 17% |
| 4. OCR read the line with character errors, so the value can never match gold | 10 | 14% |
| 11. The anchor fired and took the wrong neighbouring box as its value | 8 | 11% |
| 6. A wrapped / multi-line value was cut short or over-merged | 2 | 3% |

## Misses by field and category

| Field | recognition | unlabeled | layout | association | ocr_missed | wrapped | total |
|---|---|---|---|---|---|---|---|
| best_before | 0 | 1 | 4 | 0 | 1 | 0 | 6 |
| consumer_care | 3 | 0 | 2 | 2 | 5 | 0 | 12 |
| country_of_origin | 0 | 0 | 2 | 0 | 1 | 0 | 3 |
| generic_name | 1 | 9 | 0 | 0 | 2 | 0 | 12 |
| manufacturer | 3 | 0 | 1 | 3 | 7 | 0 | 14 |
| mfg_date | 1 | 0 | 2 | 1 | 1 | 1 | 6 |
| mrp | 0 | 2 | 2 | 1 | 2 | 0 | 7 |
| net_quantity | 2 | 0 | 1 | 1 | 2 | 1 | 7 |
| unit_sale_price | 0 | 0 | 1 | 0 | 2 | 0 | 3 |

## Spurious predictions by field

| Field | Count |
|---|---|
| manufacturer | 2 |
| mrp | 1 |
| unit_sale_price | 1 |
| mfg_date | 1 |
| generic_name | 1 |
| consumer_care | 1 |

## Every miss and spurious prediction

| Case | Field | Gold | Best OCR line (coverage, conf) | Final | Category | Why |
|---|---|---|---|---|---|---|
| ecom_amazon_britannia_tiger | mrp | — | — | M.R.P10.00 | spurious | predicted a field gold does not have |
| ecom_amazon_britannia_tiger | unit_sale_price | — | — | 9.00/100 g | spurious | predicted a field gold does not have |
| ecom_amazon_figaro_olive_oil | manufacturer | Manufacturer Deoleo SA, Deoleo SA, Ctra N-IV , km 388, 14610 Alcolea (Cordoba)- Spain. 18001030494 | Manufacturer:Deoleo SA,Deoleo SA,Ctra N-1Vkm 388,14610AlcoleaCordoba-Spain.18001030494 (36%, 0.93) | Manufacturer:Deoleo SA,Deoleo SA,Ctra N-1Vkm 388,14610AlcoleaCordoba-Spain.18001030494 | recognition | prediction is 99% similar to gold: characters OCR misread |
| ecom_amazon_parle_g_800g | mfg_date | — | — | Mfg.Date:21/12/17 | spurious | predicted a field gold does not have |
| ecom_amazon_parle_g_800g | mrp | ₹90 | amazon.in (0%, 0.98) | M.R.P10.00 | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_krackjack | mrp | ₹128 | amazon.in (0%, 0.96) | M.R.P150.00 | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_flipkart_tata_salt | manufacturer | Marketed by: TATA CONSUMER PRODUCTS LIMITED, 1, Bishop Lefroy Road, Kolkata, West Bengal - 700 020. | West Bengal-700020 (15%, 0.90) | — | layout | gold words are in the OCR output (62%) but the best single line holds 15% |
| ecom_flipkart_tata_salt | net_quantity | Quantity 1000 g | Quantity (50%, 0.99) | NET WEIGHT 1kg | association | anchor fired but the value came from another box (48% similar) |
| obf_cetaphil_moisturising_lotion_89060 | best_before | Use Before: 04/26 | FOR EXTERNAL USE ONLY. (33%, 0.91) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_cetaphil_moisturising_lotion_89060 | manufacturer | Marketed by: Galderma India Pvt. Ltd. | Marketed by:Galderma India Pvt.Ltd. (60%, 0.92) | Marketed by Galderma India Pvt.Ld Sth floor,D Wing Unit 801& 802, 6Wing 802 Lotus Corporate Park O Western Express gwy orgaon ast Mumbai400063.Maharashtra.India. For conmr k or coinwad ys orcontact+s z240 or email at io.inia@galdema.com | association | anchor fired but the value came from another box (26% similar) |
| obf_himalaya_lip_balm_8901138509231 | net_quantity | Net Wt. 10 g | Net Wt.1 g (100%, 0.94) | Net Wt.1 g | recognition | prediction is 93% similar to gold: characters OCR misread |
| obf_muuchstac_ocean_muuchstac_face_was | best_before | Exp. Dt 04/2027 | MUUCHSTAC (0%, 1.00) | — | layout | gold words are in the OCR output (50%) but the best single line holds 0% |
| obf_muuchstac_ocean_muuchstac_face_was | consumer_care | Customer Care Contact at: Address: Same as above Mob. No./: +91-9892599660 Email Id: customercare@muuchstac.com Website: www.muuchstac.com | Address: (8%, 0.99) | — | ocr_missed | only 15% of the gold words are anywhere in the OCR output |
| obf_muuchstac_ocean_muuchstac_face_was | manufacturer | MARKETED BY: Triology Solutions Pvt. Ltd. CIN: U90009MH2017PTC294630 Address: D3 Kasturi Vandana Complex, Lane Opp Swagat Hotel, Goddev Phathak Road, Bhayandar (E), Maharashtra, India - 401105 | Swagat Hotel, (9%, 0.98) | MFD.BY Universal Cosmetics Address: Plot No. 01, Survey No. 101/P, Gala No.02 & 03,Rakholi Silvassa,UT Of DNH & DD,India 396230 | ocr_missed | only 45% of the gold words are anywhere in the OCR output |
| obf_muuchstac_ocean_muuchstac_face_was | mfg_date | Mfd. 05/2025 | Mfd (50%, 0.99) | (when packed.) 05.2025 | association | anchor fired but the value came from another box (52% similar) |
| obf_muuchstac_ocean_muuchstac_face_was | mrp | MRP ₹ (Incl. of all taxes) 299.00 | ALL SKIN (20%, 0.95) | — | ocr_missed | only 40% of the gold words are anywhere in the OCR output |
| obf_muuchstac_ocean_muuchstac_face_was | net_quantity | Net Vol. 100ml (3.38 FL.OZ) (when packed.) | 100ml (3.38 FL.OZ) (43%, 0.98) | Net Vol, 100ml (3.38 FL.OZ) | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| obf_patanjali_saundarya_aloe_vera_gel_ | generic_name | AYURVEDIC PROPRIETARY MEDICINE | AYURVEDIC PROPRIETARY MEDICINE (100%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_amul_amul_masti_spiced_buttermilk_ | manufacturer | Marketed by: Gujarat Co-operative Milk Marketing Federation Ltd., Amul Dairy Road, Anand, Gujarat - 388001, India. | Marketed by: Gujarat Co-operative Milk Marketing (43%, 0.95) | Marketed by: Gujarat Co-operative Milk Marketing India Wehsit | association | anchor fired but the value came from another box (65% similar) |
| off_amul_amul_taaza_amul_taaza_milky_m | generic_name | PASTEURISED HOMOGENISED TONED MILK | TONED MILK (50%, 0.96) | TONED MILK | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_balaji_wafers_chataka_patak | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | INDIAN SNACKS & SAVOURIES (50%, 0.96) | PROPRIETARY FOOD | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_balaji_wafers_panjabi_tadka | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | 51 (0%, 0.74) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_balaji_balaji_wafers_panjabi_tadka | mfg_date | PKD. : 01JUL25 09:02:49 | PKD. : (33%, 0.94) | PKD. : 01JUL25 | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| off_balaji_balaji_wafers_panjabi_tadka | net_quantity | NET WEIGHT : 22g | NET WEIGHT: (67%, 0.94) | — | layout | gold words are in the OCR output (67%) but the best single line holds 67% |
| off_balaji_chataka_pataka_890601050211 | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | PROPRIETARY FOOD (33%, 0.96) | PROPRIETARY FOOD | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_chataka_pataka_890601050211 | unit_sale_price | UNIT SALE PRICE : ₹ 0.20 PER g | UNIT SALE PRIE3020DC (40%, 0.78) | — | layout | gold words are in the OCR output (60%) but the best single line holds 40% |
| off_bisleri_bisleri_1ltr_made_in_india | best_before | BEST BEFORE SIX MONTHS FROM MANUFACTURE | STORE IN A COOL DRY AND VENTILATED PLACE.KEEP AWAY FROM (17%, 0.93) | — | ocr_missed | only 33% of the gold words are anywhere in the OCR output |
| off_bisleri_bisleri_1ltr_made_in_india | consumer_care | CONTACT: CUSTOMER CARE EXECUTIVE 1800-121-1007 EMAIL: WECARE@BISLERI.CO.IN ADDRESS: SAME AS MKT BY ADDRESS | CONTACICUSTOMER CARE EXECUTIVE C1800-121-1007 (36%, 0.93) | CONTACICUSTOMER CARE EXECUTIVE C1800-121-1007 EMAILWECARE@BISLERI.CO.IN ADDRESS SAME AS MKT BY ADDRESS T lS @ WWW BISLERI COM NED BYPRISTINE AQUATICS MAHARASHTRA445001 UCNO.10020022011032 | association | anchor fired but the value came from another box (70% similar) |
| off_bisleri_bisleri_1ltr_made_in_india | generic_name | PACKAGED DRINKING WATER OZONISED | PACKAGEDDRINKING WATERJOZONISED (100%, 0.97) | PACKAGED DRINKING WATER | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_bisleri_bisleri_1ltr_made_in_india | manufacturer | MKT BY: BISLERI INTERNATIONAL PVT. LTD., 5TH FLOOR, CTS NO. 525/1A1/A, WESTERN EXPRESS HIGHWAY, ANDHERI (EAST), MUMBAI - 400 099, MAHARASHTRA. | Bisleri (6%, 0.99) | — | ocr_missed | only 17% of the gold words are anywhere in the OCR output |
| off_britannia_jimjam_57g_57_8901063029 | generic_name | Flavoured Sandwich Biscuits | BISCUITS NET WEIGHT (33%, 0.96) | — | ocr_missed | only 33% of the gold words are anywhere in the OCR output |
| off_britannia_marie_gold_biscuit_89010 | generic_name | BISCUIT | BISCUIT (100%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_britannia_marie_gold_biscuit_89010 | mrp | MRP. ₹10.00 (INCL. OF ALL TAXES) | O OO CINCLOFALL TAXES  OI (20%, 0.73) | — | layout | gold words are in the OCR output (60%) but the best single line holds 20% |
| off_britannia_marie_gold_biscuit_89010 | unit_sale_price | Rs. 0.16 P.G. | SCAN&GET (0%, 0.94) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_bru_bru_instant_coffee_89010305358 | best_before | USE BY 23/01/26 | 24/01/25 23/01/26 RA22 (50%, 0.95) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_bru_bru_instant_coffee_89010305358 | consumer_care | LEVERCARE-QUERY / FEEDBACK, TOLL FREE: 1800-10-22-221, PO BOX 14760, MUMBAI 400 099, LEVER.CARE@UNILEVER.COM | /FEEDBACK, (9%, 0.97) | — | ocr_missed | only 36% of the gold words are anywhere in the OCR output |
| off_bru_bru_instant_coffee_89010305358 | generic_name | INSTANT COFFEE-CHICORY MIXTURE COFFEE 70% CHICORY 30% | NSTANT COFFEE-CHICORY (60%, 0.97) | NSTANT COFFEE-CHICORY | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_bru_bru_instant_coffee_89010305358 | manufacturer | MKTD. BY: HINDUSTAN UNILEVER LTD. (HUL), UNILEVER HOUSE, CHAKALA, ANDHERI (E), MUMBAI-99. | RIGNAROMA (0%, 0.88) | — | ocr_missed | only 20% of the gold words are anywhere in the OCR output |
| off_bru_bru_instant_coffee_89010305358 | mfg_date | PKD. 24/01/25 | 24/01/25 23/01/26 RA22 (50%, 0.95) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_ching_s_secret_schezwan_chutney_89 | consumer_care | FOR ANY COMPLAINT CONTACT CUSTOMER CARE EXECUTIVE AT MKT BY ADDRESS ABOVE. 18001084488 AND care@tataconsumer.com | *Based on 2000 kcal diet recommended for Adult (8%, 0.98) | — | ocr_missed | only 31% of the gold words are anywhere in the OCR output |
| off_ching_s_secret_schezwan_chutney_89 | manufacturer | MKT BY: CAPITAL FOODS PVT. LTD., VILLA CAPITAL, SADHANA COMPOUND, NR. OSHIWARA BRIDGE, S. V. ROAD, JOGESHWARI (W), MUMBAI - 400 102. | MKT BYCAPITAL FOODS PVT.LTD. (25%, 0.93) | — | ocr_missed | only 38% of the gold words are anywhere in the OCR output |
| off_ching_secret_dark_soy_sauce_890159 | consumer_care | FOR ANY COMPLAINT CONTACT CONSUMER MANAGER AT BRAND OWNED & MARKETED BY ADDRESS ABOVE. 022-67140100 AND CUSTOMERCARE@CAPITALFOODS.CO.IN | FOR ANY COMPLAINT (21%, 0.92) | — | ocr_missed | only 29% of the gold words are anywhere in the OCR output |
| off_ching_secret_dark_soy_sauce_890159 | generic_name | DARK SOY SAUCE (SOYABEAN SAUCE) | (SOYABEAN SAUCE) (60%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_ching_secret_dark_soy_sauce_890159 | manufacturer | BRAND OWNED & MARKETED BY: CAPITAL FOODS PVT.LTD., VILLA CAPITAL, SADHANA COMPOUND, NR. OSHIWARA BRIDGE, S.V. ROAD, JOGESHWARI (W), MUMBAI - 400 102. | Ching's (0%, 0.97) | — | ocr_missed | only 12% of the gold words are anywhere in the OCR output |
| off_ching_secret_dark_soy_sauce_890159 | mfg_date | DATE OF MFG.: 10/12/2024 (15:16) | DATE OF MFG: (50%, 0.87) | DATE OFMFG: USERY 10/12/202415:16) | recognition | prediction is 90% similar to gold: characters OCR misread |
| off_ching_secret_dark_soy_sauce_890159 | mrp | MRP ₹: (incl. of all taxes) 25 (Rs. 0.28/g) | incl. of all taxes (60%, 0.89) | MRP: 25Rs.0.28/9) | association | anchor fired but the value came from another box (56% similar) |
| off_ching_secret_dark_soy_sauce_890159 | unit_sale_price | Rs. 0.28/g | Ching's (0%, 0.97) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_coca_cola_sprite_8901764032707 | country_of_origin | MADE IN INDIA | Sprite (0%, 0.99) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_coca_cola_sprite_8901764032707 | generic_name | — | — | CARBONATED WATER | spurious | predicted a field gold does not have |
| off_coca_cola_sprite_8901764032707 | net_quantity | NET QUANTITY: 600 ml | 600 ml (33%, 0.93) | — | ocr_missed | only 33% of the gold words are anywhere in the OCR output |
| off_coca_cola_sprite_sprite_8901764032 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS: SAME AS MFG/MKT BY ADDRESS | ADDRESS SAME AS MANOFACTURED BADDRESS (30%, 0.94) | — | layout | gold words are in the OCR output (60%) but the best single line holds 30% |
| off_coca_cola_sprite_sprite_8901764032 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS : SAME AS MANUFACTURED BY ADDRESS | CONTACT CONSUMERIES (20%, 0.87) | — | layout | gold words are in the OCR output (60%) but the best single line holds 20% |
| off_coca_cola_sprite_sprite_8901764032 | manufacturer | MANUFACTURED BY BENGAL BEVERAGES PVT. LTD., (UNIT-II), DURGAPUR EXPRESSWAY, P.O. DANKUNI COAL COMPLEX, DIST: HOOGHLY - 712 310, WEST BENGAL | MANUFACTURED BY BENGAL BEVERAGES PVT.LTD (24%, 0.95) | MANUFACTURED BY BENGAL BEVERAGES PVT.LTD (UNIT-N1).DURGAPUR EXPRESSWAT.P.O.OANKUNICOAL COMPLEX,DIST:HOOGHLY-712 310.WESTBENGAL ssalLic No.1001203100008 | recognition | prediction is 87% similar to gold: characters OCR misread |
| off_coke_diet_coke_can_250ml_890176406 | best_before | BEST BEFORE THREE MONTHS FROM MANUFACTURE WHEN STORED IN A COOL AND DRY PLACE | WHEN STORED IN A COOL AND DRY PLACE (50%, 0.92) | — | layout | gold words are in the OCR output (100%) but the best single line holds 50% |
| off_coke_diet_coke_can_250ml_890176406 | consumer_care | — | — | CONTACT CONSUMER RESPONSE CO 1800-208-2653indiahe | spurious | predicted a field gold does not have |
| off_coke_diet_coke_can_250ml_890176406 | manufacturer | — | — | MANUFACTURED BY:KANDHARI BEVERAGS PLOT NO.460HSIDC INDUSTRIAL GROW CENTERSAHA-133104DISTT.AMBALA.H | spurious | predicted a field gold does not have |
| off_haldiram_phalhari_chiwda_890400440 | best_before | USE BY: 23.11.25 | 23.11.25(18L) (50%, 0.95) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_haldiram_phalhari_chiwda_890400440 | mfg_date | MFG. DATE: 24.06.25 | 24.06.25 (33%, 0.98) | — | layout | gold words are in the OCR output (100%) but the best single line holds 33% |
| off_hindustan_coca_cola_beverages_pvt_ | country_of_origin | MADE IN INDIA | ORIGINAL (0%, 1.00) | — | layout | gold words are in the OCR output (50%) but the best single line holds 0% |
| off_hindustan_coca_cola_beverages_pvt_ | manufacturer | — | — | AS MFG BY ADDRESS | spurious | predicted a field gold does not have |
| off_kinley_kinley_mineral_water_1ltr_8 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS : SAME AS MFG BY ADDRESS | ADDRESS SAME AS MFG BY ADDRESS (40%, 0.83) | — | ocr_missed | only 40% of the gold words are anywhere in the OCR output |
| off_kinley_kinley_mineral_water_1ltr_8 | country_of_origin | MADE IN INDIA | MFG BY SOUTH INDIA BOTTLING Co.PVT.LTD.B163-170 (50%, 0.92) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_kinley_kinley_mineral_water_1ltr_8 | manufacturer | MFG BY SOUTH INDIA BOTTLING Co.PVT.LTD., B163-170, SIPCOT INDL. GROWTH CENTRE, NH7, GANGAIKONDAN VILLAGE, TIRUNELVELI DIST., TAMILNADU-627352. | MFG BY SOUTH INDIA BOTTLING Co.PVT.LTD.B163-170 (38%, 0.92) | MFG BY SOUTH INDIA BOTTLING Co.PVT.LTD.B163-170 | ocr_missed | only 38% of the gold words are anywhere in the OCR output |
| off_kitkat_nestle_nutrition_kitkat_min | consumer_care | NESTLÉ CONSUMER CARE, P.O. BAG 2, NEW DELHI-110001 WECARE@IN.NESTLE.COM 1800 103 1947 | NESTLECONSUMERCARE (10%, 0.98) | NESTLECONSUMERCARE P.O.BAG2NEWDELH-100 -WECARE@IN.NESTLECOM C18001031947 ~otherthan naturallyoccrringurans tat KNOW YOUR PORTION 1 serve=11.9g.Pack contains1srve | association | anchor fired but the value came from another box (61% similar) |
| off_kitkat_nestle_nutrition_kitkat_min | mfg_date | JUL/25 - FEB/26 - 5159045481 | 10F (0%, 0.87) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_kitkat_nestle_nutrition_kitkat_min | mrp | ₹ 10/- | 10F (0%, 0.87) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_kurkure_pepsico_kurkure_masala_mun | consumer_care | THE CONSUMER SERVICES MANAGER, PEPSICO INDIA HOLDINGS PVT. LTD., P.O. BOX-27, DLF QUTAB ENCLAVE, PHASE-1, GURUGRAM - 122002, HARYANA, INDIA. OR CALL US AT 1800 22 4020 OR EMAIL US AT CONSUMER.FEEDBACK@PEPSICO.COM | PepsiCo India Holdings Pvt.Ltd (17%, 0.96) | THE CONSUMER SERVICES MANAGER PEPSICO INDIA HOLDINGS PVT.LTD., P.O.BOX-27.DLF QUTAB ENCLAVE,PHASE- GURUGRAM-122002,HARYANA,INDIA ORCALLUSAT 1800224020 OR EMAILUSAT CONSUMER.FEEDBACK@PEPSICO.COM | recognition | prediction is 100% similar to gold: characters OCR misread |
| off_mazza_the_coca_cola_company_maaza_ | manufacturer | MFG BY: HINDUSTAN COCA-COLA BEVERAGES PVT LTD, 303&304, BAANI ADDRESS 1, GOLF CRSE, SEC 53, GURUGRAM-122011, HARYANA | MFG BY:HINDUSTAN COCA-COLAEN (21%, 0.91) | MFG BY:HINDUSTAN COCA-COLAEN GURUGRAM-122011,HARYANA | ocr_missed | only 36% of the gold words are anywhere in the OCR output |
| off_pepsi_cola_pepsi_8902080104581 | consumer_care | CONTACT CUSTOMER SERVICE MANAGER AT: P.O. BOX 27, DLF QUTAB ENCLAVE-1, GURUGRAM-122002, HARYANA CONSUMER.FEEDBACK@PEPSICO.COM 1800 22 4020 | CONTACT CUSTOMER SERVICE MANAGER (31%, 0.96) | CONTACT CUSTOMER SERVICE MANAGER AT:P.O.BOX 27DLF QUTAB ENCLAVE-1, GURUGRAM-122002,HARYANA CONSUMER.FEEDBACK@PEPSICO.COM C1800224020 | recognition | prediction is 100% similar to gold: characters OCR misread |
| off_pepsi_cola_pepsi_8902080104581 | manufacturer | MFD. BY: VARUN BEVERAGES LIMITED | MFD.BY:VARUN BEVERAGESLIMITED (75%, 0.92) | MKT.BY. PEPSICO INDIA HOLDINGS PVL.LID | association | anchor fired but the value came from another box (25% similar) |
| off_pepsi_cola_pepsi_8902080104581 | net_quantity | NET QUANTITY 400 ml (250 ml + 150 ml Free) | NET QUANTITY (33%, 0.97) | NET QUANTITY (250ml+150mlFree | recognition | prediction is 91% similar to gold: characters OCR misread |
| off_pepsico_quaker_oats_8901491103794 | mrp | MRP ₹: (INCL. OF ALL TAXES) 79/- | (INCL.OF ALL TAXES) (40%, 0.93) | — | layout | gold words are in the OCR output (100%) but the best single line holds 40% |
| off_tata_tata_salt_8904043901015 | generic_name | Vacuum Evaporated Edible Common Salt | Ingredients: Edible Common Salt. Potassium (60%, 0.94) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_thumsup_thums_up_3948764042911 | net_quantity | NET QUANTITY: 250 ml | 250 ml (33%, 0.94) | — | ocr_missed | only 33% of the gold words are anywhere in the OCR output |
| phone_reynolds_jetter_classic_ballpen | consumer_care | Consumer Care Officer at the above address. Toll Free No.: 0008 0005 04348 E-mail: reynoldsindiaconsumercare@newellco.com | Toll Free No.: 0008 0005 04348 (38%, 0.99) | Consumer Care Officer at the above address. Toll Free No.: 0008 0005 04348 E-mail: reynoldsindiaconsumercare@newellco.com REYNOLDS-PENS.COM | recognition | prediction is 93% similar to gold: characters OCR misread |
| phone_reynolds_jetter_classic_ballpen | generic_name | Generic Name Ball Pen | Ceneric Name Ball Pen (75%, 0.95) | Ceneric Name Ball Pen | recognition | prediction is 94% similar to gold: characters OCR misread |
| phone_reynolds_jetter_classic_ballpen | manufacturer | Manufactured, Marketed and Brand Owned by Reynolds Pens India Private Limited, Plot No. C-21, SIPCOT Industrial Park, Irungattukottai, Sriperumbudur, Kanchipuram District, Tamil Nadu - 602 117 | Reynolds Pens India Private Limited (22%, 0.97) | Manufactured,Marketed and Brand Owned bye Reynolds Pens India Private Limited Plot No. C-21, SlPCOT Industrial Park Irungattukottai, Sriperumbudur, Kanchipuram District Tamil Nadu - 602 117 | recognition | prediction is 99% similar to gold: characters OCR misread |
