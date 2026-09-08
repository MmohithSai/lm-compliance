# Real-photo error report — `2026-09-08_audit-baseline.json`

38 real cases, 141 gold declarations, 43 correct, 98 missed or wrong, 13 spurious.

## Misses by category

| Category | Misses | Share |
|---|---|---|
| 7. The declaration is printed with no label at all (nothing to anchor on) | 26 | 27% |
| 1. OCR did not detect the text (under half the gold words are anywhere in the output) | 23 | 23% |
| 2. OCR read the words but they span several boxes and the extractor did not group them | 18 | 18% |
| 11. The anchor fired and took the wrong neighbouring box as its value | 15 | 15% |
| 6. A wrapped / multi-line value was cut short or over-merged | 9 | 9% |
| 4. OCR read the line with character errors, so the value can never match gold | 7 | 7% |

## Misses by field and category

| Field | wrapped | recognition | unlabeled | association | layout | ocr_missed | total |
|---|---|---|---|---|---|---|---|
| best_before | 2 | 0 | 1 | 2 | 3 | 1 | 9 |
| consumer_care | 0 | 2 | 0 | 1 | 4 | 5 | 12 |
| country_of_origin | 0 | 1 | 0 | 1 | 2 | 1 | 5 |
| generic_name | 0 | 0 | 17 | 0 | 1 | 2 | 20 |
| importer | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| manufacturer | 4 | 2 | 0 | 3 | 1 | 7 | 17 |
| mfg_date | 1 | 0 | 0 | 3 | 1 | 1 | 6 |
| mrp | 0 | 0 | 2 | 4 | 2 | 2 | 10 |
| net_quantity | 1 | 2 | 1 | 1 | 2 | 2 | 9 |
| unit_sale_price | 0 | 0 | 5 | 0 | 2 | 2 | 9 |

## Spurious predictions by field

| Field | Count |
|---|---|
| best_before | 4 |
| mfg_date | 3 |
| manufacturer | 3 |
| mrp | 2 |
| consumer_care | 1 |

## Every miss and spurious prediction

| Case | Field | Gold | Best OCR line (coverage, conf) | Final | Category | Why |
|---|---|---|---|---|---|---|
| ecom_amazon_britannia_tiger | manufacturer | Manufacturer : Britannia Industries Ltd, Britannia Industries Ltd | Manufacturer : Britannia Industries Ltd (100%, 0.96) | Manufacturer : Britannia Industries Ltd | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| ecom_amazon_britannia_tiger | mrp | — | — | M.R.P10.00 | spurious | predicted a field gold does not have |
| ecom_amazon_figaro_olive_oil | country_of_origin | Country of Origin España | Country of Origin (67%, 0.98) | Country of Origin Espana | recognition | prediction is 95% similar to gold: characters OCR misread |
| ecom_amazon_figaro_olive_oil | importer | Importer Deoleo India Pvt. Ltd. Notan Heights, 1st Floor, 20, Gurunanak Marg, Bandra West Mumbai-400050 India. 18001030494 | Importer:Deoleo India Pvt.Ltd.Notan Heights,1st Floor,20,Gurunanak Marg,Bandra West Mumbai-400050 India.18001030494 (75%, 0.93) | Importer Deoleo India Pvt.Ltd.Notan | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| ecom_amazon_figaro_olive_oil | manufacturer | Manufacturer Deoleo SA, Deoleo SA, Ctra N-IV , km 388, 14610 Alcolea (Cordoba)- Spain. 18001030494 | Manufacturer:Deoleo SA,Deoleo SA,Ctra N-1Vkm 388,14610AlcoleaCordoba-Spain.18001030494 (36%, 0.93) | Manufacturer Deoleo SA, Deoleo SA,Ctra N- | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| ecom_amazon_figaro_olive_oil | mfg_date | — | — | Cold Pressed Oil\|Packed in Spain \|75% MUFA\| | spurious | predicted a field gold does not have |
| ecom_amazon_figaro_olive_oil | unit_sale_price | ₹119.80 /100 ml | 119.80 /100 ml) (100%, 0.94) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_g_800g | best_before | — | — | Exp.Date:5 months | spurious | predicted a field gold does not have |
| ecom_amazon_parle_g_800g | mfg_date | — | — | Mfg.Date:21/12/17 | spurious | predicted a field gold does not have |
| ecom_amazon_parle_g_800g | mrp | ₹90 | amazon.in (0%, 0.98) | M.R.P10.00 | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_g_800g | unit_sale_price | ₹11.25 /100 g | 90 11.25 /100 g) (100%, 0.93) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_krackjack | mrp | ₹128 | amazon.in (0%, 0.96) | M.R.P150.00 | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_parle_krackjack | unit_sale_price | ₹18.29 /100 g | 12800(18.29 /100 g) (100%, 0.94) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_amazon_tata_salt_1kg | manufacturer | Manufacturer : Tata Chemicals Limited, P. 0. Mithapur-361 345, District-Devbhumi Dwarka, Gujarat, Lic. No. 10012021000351, Tata Sampann | Manufacturer : Tata Chemicals Limited,P.0.Mithapur-361 345,District-Devbhumi Dwarka,Gujarat,Lic.No.10012021000351,Tata Sampann (69%, 0.95) | Manufacturer : Tata Sampann | association | anchor fired but the value came from another box (35% similar) |
| ecom_amazon_tata_salt_1kg | unit_sale_price | ₹2.90 /100 g | (2.90 /100 g) (100%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| ecom_flipkart_tata_salt | manufacturer | Marketed by: TATA CONSUMER PRODUCTS LIMITED, 1, Bishop Lefroy Road, Kolkata, West Bengal - 700 020. | West Bengal-700020 (15%, 0.90) | — | layout | gold words are in the OCR output (62%) but the best single line holds 15% |
| ecom_flipkart_tata_salt | net_quantity | Quantity 1000 g | Quantity (50%, 0.99) | NET WEIGHT 1kg | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_cetaphil_gentle_skin_cleanser_8906 | generic_name | Gentle Skin Cleanser | Gentle Skin Cleanser (100%, 0.98) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_cetaphil_gentle_skin_cleanser_8906 | net_quantity | Net Qty.: 125 mL | Net Qty: (67%, 0.94) | — | layout | gold words are in the OCR output (100%) but the best single line holds 67% |
| obf_cetaphil_moisturising_lotion_89060 | best_before | Use Before: 04/26 | FOR EXTERNAL USE ONLY. (33%, 0.91) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_cetaphil_moisturising_lotion_89060 | generic_name | Moisturising Lotion | Moisturising Lotion (100%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_cetaphil_moisturising_lotion_89060 | manufacturer | Marketed by: Galderma India Pvt. Ltd. | Marketed by:Galderma India Pvt.Ltd. (60%, 0.92) | Manufactured by:Encube Ethicals Pvt. Ltd. Plot No.C1,Madkaim Ind.Estate,Madkaim Doot | association | anchor fired but the value came from another box (31% similar) |
| obf_cetaphil_moisturising_lotion_89060 | mrp | MRP (Inclusive of all taxes) ₹: 486.00 (Rs. 4.86/ml) | MRP (Inclusive of all taxes) (67%, 0.95) | MRP (Inclusive of all taxes) FIL1745.V00 | association | anchor fired but the value came from another box (75% similar) |
| obf_cetaphil_moisturising_lotion_89060 | unit_sale_price | Rs. 4.86/ml | 486.00Rs.4.86/ml (100%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_himalaya_lip_balm_8901138509231 | generic_name | Lip Balm | Lip Balm (100%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_himalaya_lip_balm_8901138509231 | net_quantity | Net Wt. 10 g | Net Wt.1 g (100%, 0.94) | Net Wt.1 g | recognition | prediction is 93% similar to gold: characters OCR misread |
| obf_muuchstac_ocean_muuchstac_face_was | best_before | Exp. Dt 04/2027 | MUUCHSTAC (0%, 1.00) | Exp.Dt | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| obf_muuchstac_ocean_muuchstac_face_was | consumer_care | Customer Care Contact at: Address: Same as above Mob. No./: +91-9892599660 Email Id: customercare@muuchstac.com Website: www.muuchstac.com | Address: (8%, 0.99) | — | ocr_missed | only 15% of the gold words are anywhere in the OCR output |
| obf_muuchstac_ocean_muuchstac_face_was | generic_name | FACE WASH | FACE WASH (100%, 0.96) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_muuchstac_ocean_muuchstac_face_was | manufacturer | MARKETED BY: Triology Solutions Pvt. Ltd. CIN: U90009MH2017PTC294630 Address: D3 Kasturi Vandana Complex, Lane Opp Swagat Hotel, Goddev Phathak Road, Bhayandar (E), Maharashtra, India - 401105 | Swagat Hotel, (9%, 0.98) | MFD.BY Address: Plot No. 01, Survey No. 101/P, Gala No.02 & 03,Rakholi Silvassa,UT Of DNH & DD,India 396230 | ocr_missed | only 45% of the gold words are anywhere in the OCR output |
| obf_muuchstac_ocean_muuchstac_face_was | mfg_date | Mfd. 05/2025 | Mfd (50%, 0.99) | Mfg Licno.:DNH/C/18 | association | anchor fired but the value came from another box (31% similar) |
| obf_muuchstac_ocean_muuchstac_face_was | mrp | MRP ₹ (Incl. of all taxes) 299.00 | ALL SKIN (20%, 0.95) | — | ocr_missed | only 40% of the gold words are anywhere in the OCR output |
| obf_muuchstac_ocean_muuchstac_face_was | net_quantity | Net Vol. 100ml (3.38 FL.OZ) (when packed.) | 100ml (3.38 FL.OZ) (43%, 0.98) | Net Vol, 100ml (3.38 FL.OZ) | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| obf_patanjali_saundarya_aloe_vera_gel_ | generic_name | AYURVEDIC PROPRIETARY MEDICINE | AYURVEDIC PROPRIETARY MEDICINE (100%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| obf_patanjali_saundarya_aloe_vera_gel_ | net_quantity | Net Volume: 150 ml | Net Volume: (67%, 0.95) | Net Volume'. Batch 150 ml | association | anchor fired but the value came from another box (85% similar) |
| off_amul_amul_masti_spiced_buttermilk_ | generic_name | SPICED BUTTERMILK | SPICEDBUTTERMILK (100%, 0.99) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_amul_amul_masti_spiced_buttermilk_ | manufacturer | Marketed by: Gujarat Co-operative Milk Marketing Federation Ltd., Amul Dairy Road, Anand, Gujarat - 388001, India. | Marketed by: Gujarat Co-operative Milk Marketing (43%, 0.95) | Marketed by: Gujarat Co-operative Milk Marketing India Wehsit | association | anchor fired but the value came from another box (65% similar) |
| off_amul_amul_taaza_amul_taaza_milky_m | generic_name | PASTEURISED HOMOGENISED TONED MILK | TONED MILK (50%, 0.96) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_balaji_wafers_chataka_patak | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | INDIAN SNACKS & SAVOURIES (50%, 0.96) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_balaji_wafers_chataka_patak | mrp | MRP ₹ (#INCL. OF ALL TAXES) : 5.00 | (INCL.OF ALL TAXES) (40%, 0.90) | — | layout | gold words are in the OCR output (100%) but the best single line holds 40% |
| off_balaji_balaji_wafers_panjabi_tadka | best_before | — | — | EXPIRY DATE | spurious | predicted a field gold does not have |
| off_balaji_balaji_wafers_panjabi_tadka | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | 51 (0%, 0.74) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_balaji_balaji_wafers_panjabi_tadka | mfg_date | PKD. : 01JUL25 09:02:49 | PKD. : (33%, 0.94) | PKD. : 01JUL25 | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| off_balaji_balaji_wafers_panjabi_tadka | net_quantity | NET WEIGHT : 22g | NET WEIGHT: (67%, 0.94) | — | layout | gold words are in the OCR output (67%) but the best single line holds 67% |
| off_balaji_chataka_pataka_890601050211 | generic_name | PROPRIETARY FOOD NAMKEEN INDIAN SNACKS & SAVOURIES | PROPRIETARY FOOD (33%, 0.96) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_balaji_chataka_pataka_890601050211 | mrp | MRP ₹ (*INCL. OF ALL TAXES) : 5.00 | (INCL.OF ALL TAXES) (40%, 0.88) | MRP (INCL.OF ALL TAXES) UNIT SALE PRIE3020DC | association | anchor fired but the value came from another box (68% similar) |
| off_balaji_chataka_pataka_890601050211 | unit_sale_price | UNIT SALE PRICE : ₹ 0.20 PER g | UNIT SALE PRIE3020DC (40%, 0.78) | — | layout | gold words are in the OCR output (60%) but the best single line holds 40% |
| off_bisleri_bisleri_1ltr_made_in_india | best_before | BEST BEFORE SIX MONTHS FROM MANUFACTURE | STORE IN A COOL DRY AND VENTILATED PLACE.KEEP AWAY FROM (17%, 0.93) | FORDATE OF MANUFACTURE.USE BY.BATCH NO. USP AND | ocr_missed | only 33% of the gold words are anywhere in the OCR output |
| off_bisleri_bisleri_1ltr_made_in_india | consumer_care | CONTACT: CUSTOMER CARE EXECUTIVE 1800-121-1007 EMAIL: WECARE@BISLERI.CO.IN ADDRESS: SAME AS MKT BY ADDRESS | CONTACICUSTOMER CARE EXECUTIVE C1800-121-1007 (36%, 0.93) | — | layout | gold words are in the OCR output (91%) but the best single line holds 36% |
| off_bisleri_bisleri_1ltr_made_in_india | generic_name | PACKAGED DRINKING WATER OZONISED | PACKAGEDDRINKING WATERJOZONISED (100%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_bisleri_bisleri_1ltr_made_in_india | manufacturer | MKT BY: BISLERI INTERNATIONAL PVT. LTD., 5TH FLOOR, CTS NO. 525/1A1/A, WESTERN EXPRESS HIGHWAY, ANDHERI (EAST), MUMBAI - 400 099, MAHARASHTRA. | Bisleri (6%, 0.99) | — | ocr_missed | only 17% of the gold words are anywhere in the OCR output |
| off_britannia_jimjam_57g_57_8901063029 | generic_name | Flavoured Sandwich Biscuits | BISCUITS NET WEIGHT (33%, 0.96) | — | ocr_missed | only 33% of the gold words are anywhere in the OCR output |
| off_britannia_jimjam_57g_57_8901063029 | mfg_date | — | — | For Mfg-unit address & Lic. No.read the last two characters of 001129 | spurious | predicted a field gold does not have |
| off_britannia_marie_gold_biscuit_89010 | generic_name | BISCUIT | BISCUIT (100%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_britannia_marie_gold_biscuit_89010 | mrp | MRP. ₹10.00 (INCL. OF ALL TAXES) | O OO CINCLOFALL TAXES  OI (20%, 0.73) | — | layout | gold words are in the OCR output (60%) but the best single line holds 20% |
| off_britannia_marie_gold_biscuit_89010 | unit_sale_price | Rs. 0.16 P.G. | SCAN&GET (0%, 0.94) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_bru_bru_instant_coffee_89010305358 | best_before | USE BY 23/01/26 | 24/01/25 23/01/26 RA22 (50%, 0.95) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_bru_bru_instant_coffee_89010305358 | consumer_care | LEVERCARE-QUERY / FEEDBACK, TOLL FREE: 1800-10-22-221, PO BOX 14760, MUMBAI 400 099, LEVER.CARE@UNILEVER.COM | /FEEDBACK, (9%, 0.97) | — | ocr_missed | only 36% of the gold words are anywhere in the OCR output |
| off_bru_bru_instant_coffee_89010305358 | generic_name | INSTANT COFFEE-CHICORY MIXTURE COFFEE 70% CHICORY 30% | NSTANT COFFEE-CHICORY (60%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_bru_bru_instant_coffee_89010305358 | manufacturer | MKTD. BY: HINDUSTAN UNILEVER LTD. (HUL), UNILEVER HOUSE, CHAKALA, ANDHERI (E), MUMBAI-99. | RIGNAROMA (0%, 0.88) | — | ocr_missed | only 20% of the gold words are anywhere in the OCR output |
| off_bru_bru_instant_coffee_89010305358 | mfg_date | PKD. 24/01/25 | 24/01/25 23/01/26 RA22 (50%, 0.95) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_ching_s_secret_schezwan_chutney_89 | consumer_care | FOR ANY COMPLAINT CONTACT CUSTOMER CARE EXECUTIVE AT MKT BY ADDRESS ABOVE. 18001084488 AND care@tataconsumer.com | *Based on 2000 kcal diet recommended for Adult (8%, 0.98) | — | ocr_missed | only 31% of the gold words are anywhere in the OCR output |
| off_ching_s_secret_schezwan_chutney_89 | manufacturer | MKT BY: CAPITAL FOODS PVT. LTD., VILLA CAPITAL, SADHANA COMPOUND, NR. OSHIWARA BRIDGE, S. V. ROAD, JOGESHWARI (W), MUMBAI - 400 102. | MKT BYCAPITAL FOODS PVT.LTD. (25%, 0.93) | — | ocr_missed | only 38% of the gold words are anywhere in the OCR output |
| off_ching_secret_dark_soy_sauce_890159 | best_before | USE BY: 10/12/2025 | USE BY: (50%, 0.93) | USE BY: incl.of all taxes | association | anchor fired but the value came from another box (29% similar) |
| off_ching_secret_dark_soy_sauce_890159 | consumer_care | FOR ANY COMPLAINT CONTACT CONSUMER MANAGER AT BRAND OWNED & MARKETED BY ADDRESS ABOVE. 022-67140100 AND CUSTOMERCARE@CAPITALFOODS.CO.IN | FOR ANY COMPLAINT (21%, 0.92) | — | ocr_missed | only 29% of the gold words are anywhere in the OCR output |
| off_ching_secret_dark_soy_sauce_890159 | generic_name | DARK SOY SAUCE (SOYABEAN SAUCE) | (SOYABEAN SAUCE) (60%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_ching_secret_dark_soy_sauce_890159 | manufacturer | BRAND OWNED & MARKETED BY: CAPITAL FOODS PVT.LTD., VILLA CAPITAL, SADHANA COMPOUND, NR. OSHIWARA BRIDGE, S.V. ROAD, JOGESHWARI (W), MUMBAI - 400 102. | Ching's (0%, 0.97) | — | ocr_missed | only 12% of the gold words are anywhere in the OCR output |
| off_ching_secret_dark_soy_sauce_890159 | mfg_date | DATE OF MFG.: 10/12/2024 (15:16) | DATE OF MFG: (50%, 0.87) | DATE OF MFG: 25Rs.0.28/9) | association | anchor fired but the value came from another box (55% similar) |
| off_ching_secret_dark_soy_sauce_890159 | mrp | MRP ₹: (incl. of all taxes) 25 (Rs. 0.28/g) | incl. of all taxes (60%, 0.89) | MRP: AA4L10002502) | association | anchor fired but the value came from another box (40% similar) |
| off_ching_secret_dark_soy_sauce_890159 | unit_sale_price | Rs. 0.28/g | Ching's (0%, 0.97) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_coca_cola_sprite_8901764032707 | country_of_origin | MADE IN INDIA | Sprite (0%, 0.99) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_coca_cola_sprite_8901764032707 | net_quantity | NET QUANTITY: 600 ml | 600 ml (33%, 0.93) | — | ocr_missed | only 33% of the gold words are anywhere in the OCR output |
| off_coca_cola_sprite_sprite_8901764032 | best_before | — | — | EXPIRY BAICH | spurious | predicted a field gold does not have |
| off_coca_cola_sprite_sprite_8901764032 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS: SAME AS MFG/MKT BY ADDRESS | ADDRESS SAME AS MANOFACTURED BADDRESS (30%, 0.94) | — | layout | gold words are in the OCR output (60%) but the best single line holds 30% |
| off_coca_cola_sprite_sprite_8901764032 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS : SAME AS MANUFACTURED BY ADDRESS | CONTACT CONSUMERIES (20%, 0.87) | — | layout | gold words are in the OCR output (60%) but the best single line holds 20% |
| off_coca_cola_sprite_sprite_8901764032 | country_of_origin | MADE IN INDIA | MADEIN INDIA (50%, 0.98) | A QUALITY PRODUCT OF | association | anchor fired but the value came from another box (14% similar) |
| off_coca_cola_sprite_sprite_8901764032 | manufacturer | MANUFACTURED BY BENGAL BEVERAGES PVT. LTD., (UNIT-II), DURGAPUR EXPRESSWAY, P.O. DANKUNI COAL COMPLEX, DIST: HOOGHLY - 712 310, WEST BENGAL | MANUFACTURED BY BENGAL BEVERAGES PVT.LTD (24%, 0.95) | MANUFACTURED BY BENGAL BEVERAGES PVT.LTD (UNIT-N1).DURGAPUR EXPRESSWAT.P.O.OANKUNICOAL COMPLEX,DIST:HOOGHLY-712 310.WESTBENGAL ssalLic No.1001203100008 | recognition | prediction is 87% similar to gold: characters OCR misread |
| off_coke_diet_coke_can_250ml_890176406 | best_before | BEST BEFORE THREE MONTHS FROM MANUFACTURE WHEN STORED IN A COOL AND DRY PLACE | WHEN STORED IN A COOL AND DRY PLACE (50%, 0.92) | — | layout | gold words are in the OCR output (100%) but the best single line holds 50% |
| off_coke_diet_coke_can_250ml_890176406 | consumer_care | — | — | CONTACT CONSUMER RESPONSE CO 1800-208-2653indiahe ADDRESS:SAMEASMANUFACTUREDBY FORDATE OFMANUFACTURE BATCHNO "BEST BEFORETHREEMONTHS FROMMANUFACTIE WHEN STORED IN A COOL AND DRY PLACE | spurious | predicted a field gold does not have |
| off_coke_diet_coke_can_250ml_890176406 | generic_name | CARBONATED WATER | CARBONATED WATER (100%, 0.97) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_coke_diet_coke_can_250ml_890176406 | manufacturer | — | — | MANUFACTURED BY:KANDHARI BEVERAGS PLOT NO.460HSIDC INDUSTRIAL GROW CENTERSAHA-133104DISTT.AMBALA.H | spurious | predicted a field gold does not have |
| off_haldiram_phalhari_chiwda_890400440 | best_before | USE BY: 23.11.25 | 23.11.25(18L) (50%, 0.95) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_haldiram_phalhari_chiwda_890400440 | mfg_date | MFG. DATE: 24.06.25 | 24.06.25 (33%, 0.98) | MFG. ७O | association | anchor fired but the value came from another box (30% similar) |
| off_hindustan_coca_cola_beverages_pvt_ | country_of_origin | MADE IN INDIA | ORIGINAL (0%, 1.00) | — | layout | gold words are in the OCR output (50%) but the best single line holds 0% |
| off_hindustan_coca_cola_beverages_pvt_ | manufacturer | — | — | AS MFG BY ADDRESS PPN BRAND AAACH3005M THE COCA-CO ARR | spurious | predicted a field gold does not have |
| off_kinley_kinley_mineral_water_1ltr_8 | best_before | BEST BEFORE TWELVE MONTHS FROM MANUFACTURE | BEST BEFORE TWELVE MONTHS (67%, 0.96) | BEST BEFORE TWELVE MONTHS | wrapped | prediction is a prefix / part of gold: continuation lines were dropped |
| off_kinley_kinley_mineral_water_1ltr_8 | consumer_care | CONTACT CONSUMER RESPONSE COORDINATOR AT: 1800-208-2653 indiahelpline@coca-cola.com ADDRESS : SAME AS MFG BY ADDRESS | ADDRESS SAME AS MFG BY ADDRESS (40%, 0.83) | — | ocr_missed | only 40% of the gold words are anywhere in the OCR output |
| off_kinley_kinley_mineral_water_1ltr_8 | country_of_origin | MADE IN INDIA | MFG BY SOUTH INDIA BOTTLING Co.PVT.LTD.B163-170 (50%, 0.92) | — | layout | gold words are in the OCR output (50%) but the best single line holds 50% |
| off_kinley_kinley_mineral_water_1ltr_8 | manufacturer | MFG BY SOUTH INDIA BOTTLING Co.PVT.LTD., B163-170, SIPCOT INDL. GROWTH CENTRE, NH7, GANGAIKONDAN VILLAGE, TIRUNELVELI DIST., TAMILNADU-627352. | MFG BY SOUTH INDIA BOTTLING Co.PVT.LTD.B163-170 (38%, 0.92) | MFG BY SOUTH INDIA BOTTLING Co.PVT.LTD.B163-170 | ocr_missed | only 38% of the gold words are anywhere in the OCR output |
| off_kissan_mixed_fruit_jam_89010309227 | best_before | — | — | PKD.USE BY&BATCH NO | spurious | predicted a field gold does not have |
| off_kitkat_nestle_nutrition_kitkat_min | consumer_care | NESTLÉ CONSUMER CARE, P.O. BAG 2, NEW DELHI-110001 WECARE@IN.NESTLE.COM 1800 103 1947 | -WECARE@IN.NESTLECOM (10%, 0.88) | — | layout | gold words are in the OCR output (80%) but the best single line holds 10% |
| off_kitkat_nestle_nutrition_kitkat_min | generic_name | Coated Wafer | Coated Wafer (100%, 0.96) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_kitkat_nestle_nutrition_kitkat_min | mfg_date | JUL/25 - FEB/26 - 5159045481 | 10F (0%, 0.87) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_kitkat_nestle_nutrition_kitkat_min | mrp | ₹ 10/- | 10F (0%, 0.87) | — | ocr_missed | only 0% of the gold words are anywhere in the OCR output |
| off_kurkure_pepsico_kurkure_masala_mun | consumer_care | THE CONSUMER SERVICES MANAGER, PEPSICO INDIA HOLDINGS PVT. LTD., P.O. BOX-27, DLF QUTAB ENCLAVE, PHASE-1, GURUGRAM - 122002, HARYANA, INDIA. OR CALL US AT 1800 22 4020 OR EMAIL US AT CONSUMER.FEEDBACK@PEPSICO.COM | PepsiCo India Holdings Pvt.Ltd (17%, 0.96) | THE CONSUMER SERVICES MANAGER PEPSICO INDIA HOLDINGS PVT.LTD., P.O.BOX-27.DLF QUTAB ENCLAVE,PHASE- GURUGRAM-122002,HARYANA,INDIA ORCALLUSAT 1800224020 OR EMAILUSAT CONSUMER.FEEDBACK@PEPSICO.COM | recognition | prediction is 100% similar to gold: characters OCR misread |
| off_kurkure_pepsico_kurkure_masala_mun | generic_name | PROPRIETARY FOOD - NAMKEEN (15.1) | PROPRIETARYFOOD-NAMKEEN (15.1) (75%, 0.95) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_kurkure_pepsico_kurkure_masala_mun | manufacturer | MARKETED BY: PepsiCo India Holdings Pvt. Ltd. | PepsiCo India Holdings Pvt.Ltd (50%, 0.96) | MARKETED BY: PepsiCo India Holdings Pvt.Ltd fssat Lic.No.10014064000435 | wrapped | gold is inside the prediction: neighbouring lines were merged in |
| off_mazza_the_coca_cola_company_maaza_ | manufacturer | MFG BY: HINDUSTAN COCA-COLA BEVERAGES PVT LTD, 303&304, BAANI ADDRESS 1, GOLF CRSE, SEC 53, GURUGRAM-122011, HARYANA | MFG BY:HINDUSTAN COCA-COLAEN (21%, 0.91) | MFG BY:HINDUSTAN COCA-COLAEN GURUGRAM-122011,HARYANA | ocr_missed | only 36% of the gold words are anywhere in the OCR output |
| off_pepsi_cola_pepsi_8902080104581 | consumer_care | CONTACT CUSTOMER SERVICE MANAGER AT: P.O. BOX 27, DLF QUTAB ENCLAVE-1, GURUGRAM-122002, HARYANA CONSUMER.FEEDBACK@PEPSICO.COM 1800 22 4020 | CONTACT CUSTOMER SERVICE MANAGER (31%, 0.96) | CONTACT CUSTOMER SERVICE MANAGER AT:P.O.BOX 27DLF QUTAB ENCLAVE-1, GURUGRAM-122002,HARYANA CONSUMER.FEEDBACK@PEPSICO.COM C1800224020 KEEP IN COOL AND DRY PLACE AWAY FROM DIRECT SUNLIGHT | association | anchor fired but the value came from another box (84% similar) |
| off_pepsi_cola_pepsi_8902080104581 | manufacturer | MFD. BY: VARUN BEVERAGES LIMITED | MFD.BY:VARUN BEVERAGESLIMITED (75%, 0.92) | MFD.BY:VARUN BEVERAGESLIMITED FOR MANUFACTURING UNIT ADDRESS ANO FSSAI LICENSE NO PLEASE SEE FIRST ONE/TWO LETTER (S) | wrapped | gold is inside the prediction: neighbouring lines were merged in |
| off_pepsi_cola_pepsi_8902080104581 | mrp | — | — | MRP INCL.OF ALL TAXES)USP. (250ml+150mlFree | spurious | predicted a field gold does not have |
| off_pepsi_cola_pepsi_8902080104581 | net_quantity | NET QUANTITY 400 ml (250 ml + 150 ml Free) | NET QUANTITY (33%, 0.97) | NET QUANTITY (250ml+150mlFree | recognition | prediction is 91% similar to gold: characters OCR misread |
| off_pepsico_quaker_oats_8901491103794 | best_before | USE BY: 05 SEP 24 | USE BY: (50%, 0.89) | USE BY: 79/- | association | anchor fired but the value came from another box (48% similar) |
| off_pepsico_quaker_oats_8901491103794 | manufacturer | — | — | MKT.BY | spurious | predicted a field gold does not have |
| off_pepsico_quaker_oats_8901491103794 | mrp | MRP ₹: (INCL. OF ALL TAXES) 79/- | (INCL.OF ALL TAXES) (40%, 0.93) | MRP (USP0.20/-perg) | association | anchor fired but the value came from another box (32% similar) |
| off_pepsico_quaker_oats_8901491103794 | unit_sale_price | USP ₹ 0.20/- per g | PER (33%, 1.00) | — | layout | gold words are in the OCR output (100%) but the best single line holds 33% |
| off_tata_tata_salt_8904043901015 | generic_name | Vacuum Evaporated Edible Common Salt | Ingredients: Edible Common Salt. Potassium (60%, 0.94) | — | unlabeled | gold carries none of the field's label words; nothing to anchor on |
| off_thumsup_thums_up_3948764042911 | net_quantity | NET QUANTITY: 250 ml | 250 ml (33%, 0.94) | — | ocr_missed | only 33% of the gold words are anywhere in the OCR output |
| phone_reynolds_jetter_classic_ballpen | consumer_care | Consumer Care Officer at the above address. Toll Free No.: 0008 0005 04348 E-mail: reynoldsindiaconsumercare@newellco.com | Toll Free No.: 0008 0005 04348 (38%, 0.99) | Consumer Care Officer at the above address. Toll Free No.: 0008 0005 04348 E-mail: reynoldsindiaconsumercare@newellco.com REYNOLDS-PENS.COM | recognition | prediction is 93% similar to gold: characters OCR misread |
| phone_reynolds_jetter_classic_ballpen | generic_name | Generic Name Ball Pen | Ceneric Name Ball Pen (75%, 0.95) | — | layout | gold words are in the OCR output (75%) but the best single line holds 75% |
| phone_reynolds_jetter_classic_ballpen | manufacturer | Manufactured, Marketed and Brand Owned by Reynolds Pens India Private Limited, Plot No. C-21, SIPCOT Industrial Park, Irungattukottai, Sriperumbudur, Kanchipuram District, Tamil Nadu - 602 117 | Reynolds Pens India Private Limited (22%, 0.97) | Manufactured,Marketed and Brand Owned bye Reynolds Pens India Private Limited Plot No. C-21, SlPCOT Industrial Park Irungattukottai, Sriperumbudur, Kanchipuram District Tamil Nadu - 602 117 | recognition | prediction is 99% similar to gold: characters OCR misread |
