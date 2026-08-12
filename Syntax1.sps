* Encoding: UTF-8.
USE ALL.
SELECT IF (analiza_valid_resolved = 1).
EXECUTE.

FREQUENCIES VARIABLES=analiza_cv_name Biased analiza_bias_type analiza_view_number analiza_total_participations.

COMPUTE include_3plus = (analiza_total_participations >= 3).
EXECUTE.

FILTER BY include_3plus.
EXECUTE.

* 1. Opisna statistika glavnih konstruktov.

DESCRIPTIVES VARIABLES=
 analiza_faktor_nezaupanje_mean
 analiza_faktor_zaupanje_mean
 analiza_skupna_ocena_zaupanja_mean
 analiza_zadovoljstvo_mean
 analiza_mm_total_correct_share
 /STATISTICS=MEAN STDDEV MIN MAX.

* 2. Izračun actionability iz Q3a-Q3g.

COMPUTE analiza_actionability_mean =
 MEAN(
 analiza_zadovoljstvo_q3a_clean_1_5,
 analiza_zadovoljstvo_q3b_clean_1_5,
 analiza_zadovoljstvo_q3c_clean_1_5,
 analiza_zadovoljstvo_q3d_clean_1_5,
 analiza_zadovoljstvo_q3e_clean_1_5,
 analiza_zadovoljstvo_q3f_clean_1_5,
 analiza_zadovoljstvo_q3g_clean_1_5
 ).
EXECUTE.

DESCRIPTIVES VARIABLES=analiza_actionability_mean
 /STATISTICS=MEAN STDDEV MIN MAX.

* 3. Graf: skupna ocena zaupanja po zaporednem ogledu.

GRAPH
 /BAR(SIMPLE)=MEAN(analiza_skupna_ocena_zaupanja_mean) BY analiza_view_number.

* 4. Graf: zadovoljstvo po zaporednem ogledu.

GRAPH
 /BAR(SIMPLE)=MEAN(analiza_zadovoljstvo_mean) BY analiza_view_number.

* 5. Graf: actionability po zaporednem ogledu.

GRAPH
 /BAR(SIMPLE)=MEAN(analiza_actionability_mean) BY analiza_view_number.

* 6. Graf: mentalni model po zaporednem ogledu.

GRAPH
 /BAR(SIMPLE)=MEAN(analiza_mm_total_correct_share) BY analiza_view_number.

* 7. Primerjava zaupanja po Biased 0/1.

EXAMINE VARIABLES=analiza_skupna_ocena_zaupanja_mean BY Biased
 /PLOT=BOXPLOT
 /STATISTICS=DESCRIPTIVES
 /MISSING=LISTWISE
 /NOTOTAL.

* 8. Primerjava zadovoljstva po Biased 0/1.

EXAMINE VARIABLES=analiza_zadovoljstvo_mean BY Biased
 /PLOT=BOXPLOT
 /STATISTICS=DESCRIPTIVES
 /MISSING=LISTWISE
 /NOTOTAL.

* 9. Primerjava mentalnega modela po Biased 0/1.

EXAMINE VARIABLES=analiza_mm_total_correct_share BY Biased
 /PLOT=BOXPLOT
 /STATISTICS=DESCRIPTIVES
 /MISSING=LISTWISE
 /NOTOTAL.

* 10. Mann-Whitney test za biased/non-biased.

NPAR TESTS
 /M-W=analiza_skupna_ocena_zaupanja_mean analiza_zadovoljstvo_mean analiza_actionability_mean analiza_mm_total_correct_share BY Biased(0 1)
 /MISSING ANALYSIS.

* 11. Spearmanove korelacije.

NONPAR CORR
 /VARIABLES=
 analiza_faktor_nezaupanje_mean
 analiza_faktor_zaupanje_mean
 analiza_skupna_ocena_zaupanja_mean
 analiza_zadovoljstvo_mean
 analiza_actionability_mean
 analiza_mm_total_correct_share
 /PRINT=SPEARMAN TWOTAIL NOSIG
 /MISSING=PAIRWISE.

* 12. Frekvence osnovnih kategorij.

FREQUENCIES VARIABLES=
 analiza_cv_name
 Biased
 analiza_bias_type
 analiza_view_number
 analiza_total_participations
 analiza_label_q3b2.
