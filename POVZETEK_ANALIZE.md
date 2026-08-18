# Povzetek analize podatkov

**Magistrsko delo:** Zaupanje skozi čas — kako razlage vplivajo na dolgoročno zaupanje v sistem umetne inteligence
**Podatki:** anketa 1KA 191776, val 11. 5. 2026
**Analiza:** Python (pandas, statsmodels), Jupyter notebook `Analiza/analiza_mesani_modeli.ipynb`

---

## 1. Vzorec

| | |
|---|---:|
| Vseh vrstic v izvozu | 388 |
| Zaključenih, brez testnih vnosov | 268 |
| **Veljavnih enot za analizo** | **267** |
| **Udeležencev** | **82** |
| Obdobje zbiranja | 4. 3. – 10. 4. 2026 (37 dni) |
| Povprečno vključen posameznik | 19 dni |

**Število opravljenih krogov na udeleženca:**

| Krogov | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|
| Udeležencev | 10 | 10 | 23 | 29 | 8 | 2 |

Eksperiment je bil zasnovan na šestih zaporednih ogledih, dokončala sta jih **dva udeleženca**. Povprečje je 3,3 kroga. Trije ali več krogov: 62 od 82 (76 %).

Zaupanje in nezaupanje imata N = 238 namesto 267, ker je 29 enot izpolnilo starejšo različico lestvice zaupanja, ki je ni mogoče primerjati z novo.

---

## 2. Popravki v pripravi podatkov

Med pripravo analize so bile odkrite tri napake v skripti za obdelavo izvoza. Vse so bile potrjene z uradnim sumarnikom 1KA (`export_sums_191776`).

**2.1 Lestvica Q2 (zadovoljstvo z razlago).** Q2a–Q2h je merjen na 7-stopenjski lestvici, skripta pa je uporabljala funkcijo za 5-stopenjsko lestvico. Vse ocene 6 in 7 so bile zavržene kot neveljavne — pri Q2a 44 % odgovorov. Ker so bili izbrisani sistematično najvišji odgovori, je bilo povprečje pristransko navzdol.

**2.2 Obračanje lestvice Q4B (nezaupanje).** Q4Ba–Q4Be je 5-stopenjska lestvica, obrnjena pa je bila po formuli za 7-stopenjsko. Rezultat je imel razpon 3–7 namesto 1–5.

**2.3 Združevanje dveh lestvic.** Q2 (1–7) in Q3 (1–5) sta bila povprečena v eno spremenljivko kljub različnima razponoma. Razklopljena sta na `analiza_zadovoljstvo_q2_mean` in `analiza_izvedljivost_q3_mean`.

**Preverjanje popravkov proti uradnemu sumarniku 1KA:**

| Spremenljivka | 1KA | Po popravku | Pred popravkom |
|---|---:|---:|---:|
| Zadovoljstvo z razlago | 4,61 | **4,61** | 3,77 |
| Zaupanje | 4,07 | **4,05** | 4,05 |
| Nezaupanje | 2,78 | **2,79** | 4,79 |

Pred popravkom se je ujemalo le zaupanje. Za analizo je treba uporabljati različico podatkov **v13** ali novejšo.

---

## 3. Zanesljivost merskih lestvic

| Dimenzija | Postavke | Lestvica | Cronbach α | N |
|---|---|---|---:|---:|
| Zaupanje | Q4Aa–Q4Ag | 1–7 | 0,946 | 238 |
| Nezaupanje | Q4Ba–Q4Be | 1–5 | 0,808 | 238 |
| Zadovoljstvo z razlago | Q2a–Q2h | 1–7 | 0,934 | 267 |
| Izvedljivost | Q3a–Q3g | 1–5 | 0,892 | 267 |
| Mentalni model | 11 nalog | delež 0–1 | — | 267 |

Vse lestvice so zanesljive.

---

## 4. Rezultati mešanih modelov

**Uporabljena specifikacija:**

```
odvisna_spremenljivka ~ analiza_view_number * Biased  + (1 | ID udeleženca)
```

Interakcija časa in pristranskosti, naključni presek po udeležencu.

**Rezultati (p-vrednosti):**

| Dimenzija | čas | Biased | interakcija |
|---|---:|---:|---:|
| Zaupanje | 0,144 | 0,823 | 0,853 |
| Nezaupanje | 0,843 | 0,617 | 0,625 |
| Zadovoljstvo z razlago | 0,665 | 0,140 | 0,119 |
| Mentalni model | 0,107 | 0,381 | 0,413 |

**Noben učinek ni statistično značilen.**

Razširjeni model `zaupanje ~ čas * bias * pravilnost MM` prav tako ne pokaže značilnih učinkov. Edini mejni člen je pravilnost mentalnega modela sama (b = −2,10, p = 0,089), in sicer z negativnim predznakom: boljše razumevanje sistema pomeni **nižje** zaupanje.

---

## 5. Dodatna analiza: kodiranje pristranskosti

V zasnovi obstajata dve nasprotni vrsti pristranskosti — pozitivna (Živa Kopitar) in negativna (Amira Bašić). Binarna spremenljivka `Biased` ju združi v isto kategorijo, zato se nasprotna učinka med seboj odštejeta.

**Primerjava na dejanskih podatkih (zaupanje):**

| Kodiranje | Koeficient | p |
|---|---:|---:|
| Binarno (0/1) | −0,018 | 0,894 |
| Trinivojsko — pozitivni bias | +0,337 | 0,063 |
| Trinivojsko — negativni bias | −0,336 | 0,052 |

**S trinivojskim kodiranjem se pojavijo značilni učinki:**

| Dimenzija | Učinek | b | p |
|---|---|---:|---:|
| Zadovoljstvo z razlago | pozitivni bias | +0,361 | **0,012** |
| Zadovoljstvo z razlago | negativni bias | −0,295 | **0,033** |
| Izvedljivost | negativni bias | −0,274 | **0,002** |

Predlog za razpravo: ali osnovno specifikacijo dopolniti s trinivojskim kodiranjem kot dodatno analizo.

---

## 6. Preverjanje predpostavk

**Kar potrjuje izbrano metodo:**

- **ICC med 0,365 in 0,604** — od 37 % do 60 % variance izvira iz razlik med udeleženci. Naključni presek je nujen; navadni testi bi bili napačni.
- **Linearni potek časa je upravičen** — primerjava AIC (čas kot kovariata proti faktorju) govori v prid zvezni obliki pri vseh petih dimenzijah.
- **Naključni učinki so normalno porazdeljeni.**
- Napovedi ne padejo izven meja lestvic, ni težav s konvergenco.

**Kar je treba poročati kot omejitev:**

- **Heteroskedastičnost** pri zaupanju (ρ = −0,228), izvedljivosti (−0,219) in zadovoljstvu (−0,201), vse p < 0,001. Razpršenost se zmanjšuje pri višjih vrednostih — tipično za omejene lestvice. Standardne napake so lahko rahlo pristranske.
- **Ostanki blago odstopajo od normalne porazdelitve** (Shapiro p < 0,05 pri štirih od petih), a asimetrija (−0,62 do 0,19) in sploščenost (−0,52 do 1,32) sta v sprejemljivih mejah. Mešani modeli so na to robustni.

---

## 7. Ugotovitve, ki presegajo modele

**7.1 Razkorak med zaznanim in dejanskim razumevanjem**

| | |
|---|---:|
| Udeleženci, ki so navedli »Ne razumem razlage« | 3,0 % |
| Pravilnost nalog mentalnega modela | 0,38 |
| Pravilna napoved ocene sistema | 0,49 |

Udeleženci so menili, da razlage razumejo, objektivno pa so rešili 38 % nalog. Napoved ocene sistema je bila pravilna v polovici primerov, kar je blizu ugibanju. To se navezuje na raziskovalno vprašanje o prekomernem zaupanju.

**7.2 Zaupanje in nezaupanje sta neodvisna** (r = 0,09). Potrjuje odločitev, da se merita kot ločena konstrukta, skladno z Visser et al. (2025).

**7.3 Zadovoljstvo in izvedljivost verjetno merita isto** (r = 0,79). Po popravku za zanesljivost približno 0,87. Predpostavka o dveh ločenih konstruktih tu ne vzdrži.

**7.4 Mentalni model ni povezan s samoocenami** (r med −0,13 in 0,12). Objektivno razumevanje sistema je nepovezano z zaupanjem in zadovoljstvom.

---

## 8. Odprta vprašanja

1. **Spremenljivka »zaznana napaka«** za raziskovalno vprašanje o zaznavi napak še ne obstaja. Kandidati iz obstoječih podatkov:

   | | Vir | Kaj meri | Povprečje |
   |---|---|---|---:|
   | A | Q3B, smiselnost razlage | prikazan **enoten** primer za vse | 0,88 |
   | B | Q3B, prosti opis spornega | omemba spola/nacionalnosti | 0,08 |
   | C | Q3A, prosti opis lastnega primera | | 0,22 |

   Ključna razlika: Q3B vsem prikaže isti primer razlage, ne njihovega lastnega življenjepisa. Za zaznavo pristranskosti v lastnem primeru je ustrezen le Q3A. Ker gre za dvojiški izid, je potreben logistični mešani model.

2. **Kodiranje pristranskosti** — binarno po specifikaciji ali trinivojsko (razdelek 5).

3. **Zadovoljstvo in izvedljivost** — obdržati ločeno in utemeljiti, ali združiti (razdelek 7.3). Faktorska analiza teh 15 postavk bi vprašanje razrešila.

4. **Ni kontrolne skupine brez razlag.** Prvotni načrt je predvideval primerjavo skupine z razlagami in brez njih; izvedeni eksperiment je imel razlage pri vseh šestih življenjepisih. Hipoteze o tem, ali razlage same povečajo zaupanje, ni mogoče testirati kot primerjavo med pogojema.

5. **Besedilo vprašanj Q4A in Q4B.** Navodilo se glasi »Razvrstite … od najpomembnejšega (1) do najmanj pomembnega (7)«, kar opisuje razvrščanje, postavke pa so trditve o zaupanju. Preverjeno: 97,5 % udeležencev je odgovarjalo kot na lestvici strinjanja (ponovljene vrednosti v vrstici), zato so podatki uporabni. Napako je treba navesti med omejitvami.

6. **Pristranskost je vezana na dva konkretna življenjepisa**, zato učinka pristranskosti ni mogoče ločiti od učinka teh dveh primerov.

7. **Trajanje.** Povprečen udeleženec je bil vključen 19 dni. Za trditev o *dolgoročnem* zaupanju je to kratko obdobje; morda je primernejša formulacija »skozi več zaporednih interakcij«.

---

## 9. Priloge

| Datoteka | Vsebina |
|---|---|
| `Analiza/analiza_mesani_modeli.ipynb` | celotna analiza z izpisi |
| `Analiza/rezultati_mesanih_modelov.csv` | zbirna tabela vseh učinkov |
| `Analiza/grafi/01_sodelovanja.png` | število sodelovanj in odgovorov po krogih |
| `Analiza/grafi/02_povprecja_postavk.png` | povprečja postavk po sklopih |
| `Analiza/grafi/03_mentalni_model.png` | pravilnost nalog mentalnega modela |
| `Analiza/grafi/04_potek_skozi_kroge.png` | potek dimenzij skozi kroge |
