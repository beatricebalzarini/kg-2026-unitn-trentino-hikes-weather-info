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
