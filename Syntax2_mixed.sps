* Encoding: UTF-8.
* ============================================================================
* LINEARNI MEŠANI MODELI (Linear Mixed-Effects Models)
* Magistrsko delo: Zaupanje skozi čas - kako razlage vplivajo na dolgoročno
* zaupanje v sistem umetne inteligence
*
* VHODNI PODATKI: anketa191776-2026-05-11_dataset_analiza_v13.csv
*   POZOR: ne uporabljaj v12 ali starejših - vsebujejo napake pri Q2 in Q4B.
*
* Zgradba: en model na dimenzijo. V vsakem modelu sta ČAS (zaporedni ogled)
* in PRISTRANSKOST fiksna učinka, UDELEŽENEC pa naključni učinek.
* Naključni učinek pomeni, da dobi vsak udeleženec svojo izhodiščno raven,
* zato model meri spremembo znotraj osebe in ne razlik med osebami.
* ============================================================================


* ----------------------------------------------------------------------------
* 0. PRIPRAVA
* ----------------------------------------------------------------------------

* Obdrži samo veljavne enote.
SELECT IF (analiza_valid_resolved = 'True').
EXECUTE.

* MIXED zahteva numerične spremenljivke za SUBJECT in za faktorje.
AUTORECODE VARIABLES=analiza_resolved_code /INTO id_udelezenec.
AUTORECODE VARIABLES=analiza_bias_type /INTO bias_tip.
EXECUTE.

* Preveri kodiranje faktorja pristranskosti pred nadaljevanjem.
* Pričakovano: brez_biasa=180, negativni_bias_nacionalnost=45,
* pozitivni_bias_nacionalnost=42.
FREQUENCIES VARIABLES=bias_tip analiza_bias_type analiza_view_number.

* Opisna statistika vseh petih dimenzij.
DESCRIPTIVES VARIABLES=
 analiza_zadovoljstvo_q2_mean
 analiza_izvedljivost_q3_mean
 analiza_faktor_zaupanje_mean
 analiza_faktor_nezaupanje_mean
 analiza_mm_total_correct_share
 /STATISTICS=MEAN STDDEV MIN MAX.


* ----------------------------------------------------------------------------
* MODEL 1: ZAUPANJE  (Q4Aa-Q4Ag, lestvica 1-7, alfa = 0,946)
* Hipotezi H1 in H4.
* ----------------------------------------------------------------------------

MIXED analiza_faktor_zaupanje_mean BY bias_tip WITH analiza_view_number
 /FIXED=analiza_view_number bias_tip | SSTYPE(3)
 /RANDOM=INTERCEPT | SUBJECT(id_udelezenec) COVTYPE(VC)
 /METHOD=REML
 /EMMEANS=TABLES(bias_tip) COMPARE ADJ(BONFERRONI)
 /PRINT=SOLUTION TESTCOV.


* ----------------------------------------------------------------------------
* MODEL 2: NEZAUPANJE  (Q4Ba-Q4Be, lestvica 1-5, alfa = 0,808)
* Postavke so obrnjene: višja vrednost = večje nezaupanje.
* ----------------------------------------------------------------------------

MIXED analiza_faktor_nezaupanje_mean BY bias_tip WITH analiza_view_number
 /FIXED=analiza_view_number bias_tip | SSTYPE(3)
 /RANDOM=INTERCEPT | SUBJECT(id_udelezenec) COVTYPE(VC)
 /METHOD=REML
 /EMMEANS=TABLES(bias_tip) COMPARE ADJ(BONFERRONI)
 /PRINT=SOLUTION TESTCOV.


* ----------------------------------------------------------------------------
* MODEL 3: ZADOVOLJSTVO Z RAZLAGO  (Q2a-Q2h, lestvica 1-7, alfa = 0,934)
* Explanation Satisfaction Scale (Hoffman). Hipotezi H2 in H4.
* ----------------------------------------------------------------------------

MIXED analiza_zadovoljstvo_q2_mean BY bias_tip WITH analiza_view_number
 /FIXED=analiza_view_number bias_tip | SSTYPE(3)
 /RANDOM=INTERCEPT | SUBJECT(id_udelezenec) COVTYPE(VC)
 /METHOD=REML
 /EMMEANS=TABLES(bias_tip) COMPARE ADJ(BONFERRONI)
 /PRINT=SOLUTION TESTCOV.


* ----------------------------------------------------------------------------
* MODEL 4: IZVEDLJIVOST  (Q3a-Q3g, lestvica 1-5, alfa = 0,892)
* ----------------------------------------------------------------------------

MIXED analiza_izvedljivost_q3_mean BY bias_tip WITH analiza_view_number
 /FIXED=analiza_view_number bias_tip | SSTYPE(3)
 /RANDOM=INTERCEPT | SUBJECT(id_udelezenec) COVTYPE(VC)
 /METHOD=REML
 /EMMEANS=TABLES(bias_tip) COMPARE ADJ(BONFERRONI)
 /PRINT=SOLUTION TESTCOV.


* ----------------------------------------------------------------------------
* MODEL 5: MENTALNI MODEL  (delež pravilnih od 11 nalog)
* Hipoteza H4. Odvisna spremenljivka je delež, zato binomski model
* z logit povezavo, ne navadni MIXED.
* ----------------------------------------------------------------------------

GENLINMIXED
 /DATA_STRUCTURE SUBJECTS=id_udelezenec
 /FIELDS TARGET=analiza_mm_total_correct_count TRIALS=11
 /TARGET_OPTIONS DISTRIBUTION=BINOMIAL LINK=LOGIT
 /FIXED EFFECTS=analiza_view_number bias_tip USE_INTERCEPT=TRUE
 /RANDOM EFFECTS=INTERCEPT USE_INTERCEPT=FALSE SUBJECTS=id_udelezenec
 /BUILD_OPTIONS
 /EMMEANS TABLES=bias_tip COMPARE=bias_tip.


* ============================================================================
* DODATNO 1: interakcija med časom in pristranskostjo
*
* Odgovori na vprašanje, ali se učinek pristranskosti spreminja skozi čas
* (npr. ali udeleženci pristranskost pri kasnejših ogledih lažje zaznajo).
* Zaženi samo, če te to zanima - ni nujno za H1 in H4.
* ============================================================================

MIXED analiza_faktor_zaupanje_mean BY bias_tip WITH analiza_view_number
 /FIXED=analiza_view_number bias_tip analiza_view_number*bias_tip | SSTYPE(3)
 /RANDOM=INTERCEPT | SUBJECT(id_udelezenec) COVTYPE(VC)
 /METHOD=REML
 /PRINT=SOLUTION TESTCOV.


* ============================================================================
* DODATNO 2: preverjanje, ali je linearni potek časa ustrezen
*
* Model s časom kot faktorjem primerjaj z modelom s časom kot kovariato.
* Pomembno: za primerjavo z informacijskimi kriteriji mora biti METHOD=ML,
* ne REML. Nižji AIC pomeni boljše prileganje.
* ============================================================================

MIXED analiza_faktor_zaupanje_mean BY bias_tip WITH analiza_view_number
 /FIXED=analiza_view_number bias_tip | SSTYPE(3)
 /RANDOM=INTERCEPT | SUBJECT(id_udelezenec) COVTYPE(VC)
 /METHOD=ML
 /PRINT=SOLUTION.

MIXED analiza_faktor_zaupanje_mean BY bias_tip analiza_view_number
 /FIXED=analiza_view_number bias_tip | SSTYPE(3)
 /RANDOM=INTERCEPT | SUBJECT(id_udelezenec) COVTYPE(VC)
 /METHOD=ML
 /PRINT=SOLUTION.
