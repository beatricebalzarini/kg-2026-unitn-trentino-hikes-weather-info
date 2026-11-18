# Personas and Scenarios
- famiglia con bambini cerca trail semplici, percorribili con il passeggino, con punti di ristoro, prevalentemente pianeggianti
- coppia appassionata di montagna cerca trail con specifici valori di dislivello, su strade poco asfaltate da percorrere a piedi in alta montagna con landmark X
- studente principiante cerca trail percorribile in meno di 2h, raggiungibile con i mezzi, con bel tempo e con almeno 3 landmark sul percorso
- atleta MTB cerca trail percorribile in bici di tanti km, con pendenze non superiori a 15% non bagnati/neve
- anziano disabile cerca trail pianeggiante percorribile in sedia a rotelle principalemnte asfaltato, con partenza entro 2k dalla sua posizione
- alpinista appassionato cerca trail in alta montagna attrezzato, ad anello, con bivacchi 
- ragazzo X vuole organizzare una hike per il 23-15 gennaio 2027 e vorrebbe sapere quanti gradi facevano a gennaio 2026

# Competency Questions
- Questo trail/Quali trails hanno meno di X dislivello?
- Quali trails hanno una pendenza massima di X?
- Quali trails sono percorribili con il passeggino?
- Quali trails hanno punti di ristoro?
- Quali trails hanno punti per pernottare?
- Quali trails hanno un dislivello di X?
- Quali trails non hanno parti asfaltate?
- Quali trail sono percorribili in meno di X ore?
- Quali trails arrivano a X metri slm?
- Quali trails sono percorribili in bici?
- Quali trails sono raggiungibili con i mezzi pubblici?
# - Quali trails sono percorribili con bel tempo in un determinato giorno?
- Quali trails non sono bagnati?
- Quali trails non sono innevati?
- Quali trails sono percorribili in sedia a rotelle?
- Quali trails sono totalmente asfaltati?
- Quali trail sono vicino a me?
- Quali trails hanno una lunghezza di X?
- Quali trails sono attrezzati?
- Quali sentieri sono ad anello?
- Quali sentieri passano da landmark X?
- Quale è il meteo per zona X?


# Entities

trail
## cosa serve a noi
- dislivello
- pendenza
- passeggino/sedia sa rotelle
- path type
- tempo di percorrenza
- km di percorrenza
- raggiungibili con i mezzi
- attrezzate
- anello

refuge/hut
## noi
- location
- pernottamento

landmark
## noi
- poszione
- nome/identificativo

geographical region (EO)

weather condition
## noi
- pioggia/non pioggia
- neve/non neve



# log
1. abbaimo definito scenarios e personas sulla base di cio che ci evniva in mente
2. abbiamo aggiunto qualche idea sulla base del dataset
3. abbiamo aggiunto quelli con il meteo
4. abbiamo generato le CQ sulla base degli scenarios
5. abbiamo chiesto all'ai un idea per le entities -> abbiamo incluso waypoints, rifugi, tarsposrti e laghi
6. abbiamo scariacto i dataset del territorio con le query generate dall'AI
7. abbiamo cercato dataset per il meteo -> trovato con open-meteo
8. tolto gli scenarios/CQs relativi alle previsioni future perchè volevamo basarci sullo storico e avrebbe richiesto operazioni al di fuori del domaniio iniziale

# Tabella CQ → attributi → file sorgente
Usata come criterio per la pulizia dei dati: un attributo si tiene solo se compare qui o serve da collegamento tra file (id, coordinate, ISTAT).
I conteggi vengono dai `.md` dei dataset in `data/`.

| # | Competency Question | Attributi / relazioni necessari | File sorgente | Copertura e note |
|---|---|---|---|---|
| 1 | Trail con meno di X dislivello | `ascent`, `descent` | `trails` | 1146/1657. `mtb` solo 8/144, `via_ferrata` 11/29. Il resto va calcolato da DEM. |
| 2 | Pendenza massima X | `incline` per segmento, aggregato per route | `ways`, `singular_paths` (+ `mtb:scale` per MTB) | `incline` su ~2000 way su 26k. Molto sparso. Alternativa: DEM. |
| 3 | Percorribili con passeggino | `surface`, `smoothness`, `width`, `incline` per segmento; flag `stroller_friendly` | `stroller`, `full_stroller_mtb`, `ways`, `singular_paths` | `stroller` ha solo 13 route e nessun tag esplicito. Serve una regola derivata. |
| 4 | Hanno punti di ristoro | `FoodDrink` vicino al trail (spatial join); `restaurant` nei rifugi | `amenities`, `huts_landmarks`, geometria da `trails` | 3145 amenity. Dedup con `tourism=alpine_hut`/`hotel`. |
| 5 | Hanno punti per pernottare | `Hut`, `Accommodation` vicino al trail; `capacity`, `winter_room` | `huts_landmarks` (alpine_hut 235, wilderness_hut 161), `accomodations` | Join spaziale con la geometria di `trails`. |
| 6 | Dislivello di X | come #1 | `trails` | come #1 |
| 7 | Non hanno parti asfaltate | `surface` di ogni segmento, aggregato per route | `ways`, `singular_paths`, `full_stroller_mtb` | `surface` su ~60% dei way. Join per `id` dei way nei `members`. |
| 8 | Percorribili in meno di X ore | `duration:forward` in minuti | `trails` | 1158/1657. `via_ferrata` 11. Per i mancanti: stima da distanza + dislivello. |
| 9 | Arrivano a X m slm | quota massima della route | `huts_landmarks` (`ele` dei picchi/valichi vicini), DEM | **Nessun campo diretto.** `ele` solo su 2919/5749 POI. |
| 10 | Percorribili in bici | `route=mtb\|bicycle`, `mtb:scale`, `bicycle` | `mtb`, `singular_paths` (cycleway), `full_stroller_mtb` | 144 route. |
| 11 | Raggiungibili con mezzi pubblici | `TransportStop` vicino al punto di partenza | `public_transportation`, partenza da `trails` | 4948 elementi, da dedup (platform + stop_position + station). |
| 12 | *(commentata)* Bel tempo in un giorno | `good_weather`, `date` | output di `new_script.py` | Dipende dall'intervallo di date scaricato. |
| 13 | Non sono bagnati | `dry` (soglie in `new_script.py`) | output meteo | Regola derivata dalla pioggia dei 3 giorni precedenti. |
| 14 | Non sono innevati | `snow` (`snow_depth_max`, `snowfall`) | output meteo | Fascia di quota 800/1500/2200 m. |
| 15 | Percorribili in sedia a rotelle | `wheelchair`, `surface`, `smoothness`, `incline`, `width` | `singular_paths` (`wheelchair` 644), `stroller`, `full_stroller_mtb` | Tag `wheelchair` molto raro. Serve una regola come per il passeggino. |
| 16 | Totalmente asfaltati | `surface=asphalt` su tutti i segmenti | come #7 | Richiede copertura `surface` completa, altrimenti "sconosciuto". |
| 17 | Vicini a me | coordinate di partenza/geometria, distanza | `trails`, `trailheads` | Calcolo a query-time. Servono start point puliti. |
| 18 | Lunghezza X | `distance` in km | `trails` | 1193/1657. `mtb` solo 23/144. Per i mancanti: lunghezza dalla geometria. |
| 19 | Attrezzati | `via_ferrata_scale`, `cai_scale=EEA*`, `safety_rope` | `via_ferrata_routes`, `trails` (EEA ~78) | Le 29 relation non hanno `members`: non si legano ai way. |
| 20 | Ad anello | `roundtrip` oppure primo punto = ultimo | `trails` (`roundtrip` 125), `mtb` (25) | Il tag è raro: va calcolato dalla geometria. |
| 21 | Passano da landmark X | `Landmark` vicino al trail, `name`, posizione | `huts_landmarks`, `mixed_pois`, `lakes`, geometria da `trails` | Anche i `guidepost` nei `members` di `trails`. |
| 22 | Meteo per zona X | comune/cella, temperature, precipitazioni | `municipalities`, output meteo | Serve il legame zona→cella meteo. |

## Requisiti che emergono dalle persone, non dalle CQ

| Persona | Requisito | Attributi | File | Nota |
|---|---|---|---|---|
| Coppia | strade poco asfaltate, alta montagna | `surface`, `sac_scale`, quota | `ways`, `trails`, `huts_landmarks` | "Alta montagna" va definito: soglia di quota o `sac_scale`. |
| Studente | almeno 3 landmark sul percorso | conteggio di `passesBy` | `huts_landmarks`, `mixed_pois` | Aggregazione dopo lo spatial join. |
| Atleta MTB | pendenze ≤ 15% | `incline` in %, `mtb:scale` | `ways`, `mtb` | Pochi dati: vedi #2. |
| Anziano disabile | partenza entro 2 km | distanza da posizione | `trails`, `trailheads` | Query-time. |
| Alpinista | in alta quota, attrezzato, ad anello, con bivacchi | `wilderness_hut`, `shelter_type`, `via_ferrata_scale`, `roundtrip` | `huts_landmarks`, `via_ferrata_routes` | Combina #5, #19, #20. |
| Ragazzo X | temperature a gennaio 2026 | `temp_max_c`, `temp_min_c` per data | output meteo | **Lo script scarica solo 1 ott–14 nov 2026**, quindi gennaio 2026 non c'è. |

## Punti aperti per la Fase 1
- **#9 (quota massima)**: DEM oppure `ele` dei POI vicini.
- **#2 e #15 (pendenza e sedia a rotelle)**: dati sparsi, quindi o DEM e regole derivate, oppure risposte parziali.
- **#12–14 e Ragazzo X (meteo)**: fissare prima l'intervallo di date.
- Attributi che non compaiono mai in tabella (`wikidata`, `source`, `check_date`, `colour`, `osmc:symbol`, `ref:*`, tag di arredo urbano): scartabili.
