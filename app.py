def pokaz_mape(komenda, liczba_patroli, dzien_tygodnia, miesiac, typ_przestepstwa, godzina_rozpoczecia, godzina_zakonczenia):
    
    #wczytanie wymaganych bibliotek
    import numpy as np
    import pandas as pd
    import requests
    import json
    import matplotlib.pyplot as plt
    from datetime import datetime, time
    from sodapy import Socrata
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    import folium
    from folium import plugins
    from sklearn.cluster import KMeans
    
    #przekodowanie zmiennych wprowadzonych przez użytkownika
    
    dic1 = {'Poniedzialek':'Monday', 'Wtorek':'Tuesday', 'Sroda':'Wednesday', 'Czwartek':'Thursday','Piatek':'Friday','Sobota':'Saturday','Niedziela':'Sunday'}
    dzien_tygodnia=[dic1.get(n, n) for n in dzien_tygodnia]
    
    godzina_rozpoczecia=time(godzina_rozpoczecia,0,0)
    godzina_zakonczenia=time(godzina_zakonczenia,0,0)
    
    dic2 = {'PODPALENIE':'ARSON','ATAK':'ASSAULT','POBICIE':'BATTERY','WLAMANIE':'BURGLARY','NOSZENIE BRONI W MIEJSCU PUBLICZNYM':'CONCEALED CARRY LICENSE VIOLATION','NAPASC NA TLE SEKSUALNYM':'CRIM SEXUAL ASSAULT','USZKODZENIE MIENIA':'CRIMINAL DAMAGE','BEZPRAWNE WTARGNIECIE':'CRIMINAL TRESPASS','WPROWADZAJACE W BLAD PRAKTYKI':'DECEPTIVE PRACTICE','HAZARD':'GAMBLING','ZABOJSTWO':'HOMICIDE','HANDEL LUDZMI':'HUMAN TRAFFICKING','ZNIEWAGA FUNKCJONARIUSZA PUBLICZNEGO':'INTERFERENCE WITH PUBLIC OFFICER','ZASTRASZENIE':'INTIMIDATION','PORWANIE':'KIDNAPPING','NARUSZENIE WARUNKOW SPRZEDAZY ALKOHOLU':'LIQUOR LAW VIOLATION','KRADZIEZ POJAZDU':'MOTOR VEHICLE THEFT','NARKOTYKI':'NARCOTICS','NIE - KRYMINALNE':'NON - CRIMINAL','NIE-KRYMINALNE':'NON-CRIMINAL','NIE-KRYMINALNE (PRZEDMIOT WSKAZANY)':'NON-CRIMINAL (SUBJECT SPECIFIED)','OBSCENICZNOSC':'OBSCENITY','WYKROCZENIE Z UDZIALEM DZIECI':'OFFENSE INVOLVING CHILDREN','INNE Z UDZIALEM NARKOTYKOW':'OTHER NARCOTIC VIOLATION','INNY ATAK':'OTHER OFFENSE','PROSTYTUCJA':'PROSTITUTION','PUBLICZNE OBNAZANIE SIE':'PUBLIC INDECENCY','ZAKLOCANIE SPOKOJU PUBLICZNEGO':'PUBLIC PEACE VIOLATION','NAPAD':'ROBBERY','MOLESTOWANIE':'SEX OFFENSE','PRZESLADOWANIE':'STALKING','KRADZIEZ':'THEFT','NIELEGALNE POSIADANIE BRONI':'WEAPONS VIOLATION'}
        
    typ_przestepstwa=[dic2.get(n, n) for n in typ_przestepstwa]
       
    #wczytanie bazy danych przy użyciu tokenu i wyfiltrowanie przestępstw popełnionych w obrębie komendy wybranej przez użytkownika
    client = Socrata("data.cityofchicago.org", "MBVEcIkH7NcG7N4iAvFZ0JAJ4", username="gerus.ewa@gmail.com", password="Hanna930602")
    results = client.get("ijzp-q8t2", where = "year > 2015", district=komenda, limit=100000)
    df = pd.DataFrame.from_records(results)
    
    #ograniczenie wynikow do trzech ostatbich lat
    three_yrs_ago = datetime.now() - relativedelta(years=3)
    df['datetime']=pd.to_datetime(df['date'])
    df=df[df['datetime']> pd.Timestamp(datetime.date(three_yrs_ago))]
    
    #usunięcie zbędnych zmiennych
    cols = [0, 1, 2, 3, 4, 6, 8, 9, 10, 11, 13, 14, 17, 18, 19, 20, 21, 22]
    df.drop(df.columns[cols],axis=1, inplace=True)
    
    #usunięcie z bazy danych obserwacji z brakującymi wynikami
    df.dropna(axis=0, inplace=True)
    
    #duplikacja zmiennej 'date' na potrzeby późniejszych przekształceń 
    df['day']=df['date']
    
    #ekstrakcja ze zmiennej 'date' informacji na temat miesiąca i godziny
    df['month'] = pd.to_datetime(df['date']).dt.month
    df['time'] = pd.to_datetime(df['date']).dt.time
    
    #ekstrakcja ze zmiennej 'date' informacji na temat dnia tygodnia
    df['day'] = pd.to_datetime(df['day']).dt.date
    df['day'] = pd.to_datetime(df['day'])
    df['day']=df['day'].dt.weekday_name
    df=df.drop(['date'], axis=1)
    
    #aplikacja pozostalych filtrów zadanych przez użytkownika
    dzien_tygodnia=list(dzien_tygodnia)
    typ_przestepstwa=list(typ_przestepstwa)
    df=df[df['day'].isin(dzien_tygodnia)]
    df=df[df['month']==miesiac]
    df=df[df['primary_type'].isin(typ_przestepstwa)]
    df=df[df['time']>=godzina_rozpoczecia]
    df=df[df['time']<godzina_zakonczenia]
    
    #implementacja algorytmu K-Średnich
    X=df.loc[:,['latitude','longitude']]
    kmeans = KMeans(n_clusters=liczba_patroli, random_state=0).fit(X)
    labels = kmeans.predict(X)
    df['cluster'] = labels
    
    #wyznaczenie środka wyświetlanej mapy (punkt centralny Chicago)
    m = folium.Map([41.8781, -87.6298], zoom_start=11)
    
    #zapisanie zmiennych informujących o długości i szerokości geograficznej jako zmiennych liczbowych, a następnie jako macierz
    df['latitude']=pd.to_numeric(df.latitude)
    df['longitude']=pd.to_numeric(df.longitude)
    punkty = df[['latitude', 'longitude']].as_matrix()

    #zdefiniowanie kolorów, którymi następnie będą oznaczane obserwacje należące do poszczególnych klastrów
    def f(row):
        if row['cluster'] == 0:
            return 'red'
        elif row['cluster'] == 1:
            return 'green'
        elif row['cluster'] == 2:
            return 'blue'
        elif row['cluster'] == 3:
            return 'yellow'
        elif row['cluster'] == 4:
            return 'purple'
        elif row['cluster'] == 5:
            return 'pink'
        elif row['cluster'] == 6:
            return 'grey'
        elif row['cluster'] == 7:
            return 'olive'
        elif row['cluster'] == 8:
            return 'brown'
        else:
            return 'white'
        return val

    df['kolor'] = df.apply(f, axis=1)
    
    #zdefiniowanie punktów wyświetlanych na mapie
    for index, row in df.iterrows(): folium.CircleMarker([row['latitude'], row['longitude']],
                        radius=5,
                        fill= True,
                        fill_opacity=1,
                        fill_color=row['kolor'],
                        color=row['kolor'],
                        popup=df['primary_type'][index]# divvy color
                       ).add_to(m)
    a=m.add_child(plugins.HeatMap(punkty, radius=5))
    
    return a

def pokaz_tabele(komenda, liczba_patroli, dzien_tygodnia, miesiac, typ_przestepstwa, godzina_rozpoczecia, godzina_zakonczenia):
    
    #wczytanie wymaganych bibliotek
    import numpy as np
    import pandas as pd
    import requests
    import json
    import matplotlib.pyplot as plt
    from datetime import datetime, time
    from sodapy import Socrata
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    import folium
    from folium import plugins
    from sklearn.cluster import KMeans
    
    #przekodowanie zmiennych wprowadzonych przez użytkownika
    
    dic1 = {'Poniedzialek':'Monday', 'Wtorek':'Tuesday', 'Sroda':'Wednesday', 'Czwartek':'Thursday','Piatek':'Friday','Sobota':'Saturday','Niedziela':'Sunday'}
    dzien_tygodnia=[dic1.get(n, n) for n in dzien_tygodnia]
    
    godzina_rozpoczecia=time(godzina_rozpoczecia,0,0)
    godzina_zakonczenia=time(godzina_zakonczenia,0,0)
    
    dic2 = {'PODPALENIE':'ARSON','ATAK':'ASSAULT','POBICIE':'BATTERY','WLAMANIE':'BURGLARY','NOSZENIE BRONI W MIEJSCU PUBLICZNYM':'CONCEALED CARRY LICENSE VIOLATION','NAPASC NA TLE SEKSUALNYM':'CRIM SEXUAL ASSAULT','USZKODZENIE MIENIA':'CRIMINAL DAMAGE','BEZPRAWNE WTARGNIECIE':'CRIMINAL TRESPASS','WPROWADZAJACE W BLAD PRAKTYKI':'DECEPTIVE PRACTICE','HAZARD':'GAMBLING','ZABOJSTWO':'HOMICIDE','HANDEL LUDZMI':'HUMAN TRAFFICKING','ZNIEWAGA FUNKCJONARIUSZA PUBLICZNEGO':'INTERFERENCE WITH PUBLIC OFFICER','ZASTRASZENIE':'INTIMIDATION','PORWANIE':'KIDNAPPING','NARUSZENIE WARUNKOW SPRZEDAZY ALKOHOLU':'LIQUOR LAW VIOLATION','KRADZIEZ POJAZDU':'MOTOR VEHICLE THEFT','NARKOTYKI':'NARCOTICS','NIE - KRYMINALNE':'NON - CRIMINAL','NIE-KRYMINALNE':'NON-CRIMINAL','NIE-KRYMINALNE (PRZEDMIOT WSKAZANY)':'NON-CRIMINAL (SUBJECT SPECIFIED)','OBSCENICZNOSC':'OBSCENITY','WYKROCZENIE Z UDZIALEM DZIECI':'OFFENSE INVOLVING CHILDREN','INNE Z UDZIALEM NARKOTYKOW':'OTHER NARCOTIC VIOLATION','INNY ATAK':'OTHER OFFENSE','PROSTYTUCJA':'PROSTITUTION','PUBLICZNE OBNAZANIE SIE':'PUBLIC INDECENCY','ZAKLOCANIE SPOKOJU PUBLICZNEGO':'PUBLIC PEACE VIOLATION','NAPAD':'ROBBERY','MOLESTOWANIE':'SEX OFFENSE','PRZESLADOWANIE':'STALKING','KRADZIEZ':'THEFT','NIELEGALNE POSIADANIE BRONI':'WEAPONS VIOLATION'}
        
    typ_przestepstwa=[dic2.get(n, n) for n in typ_przestepstwa]
       
    #wczytanie bazy danych przy użyciu tokenu i wyfiltrowanie przestępstw popełnionych w obrębie komendy wybranej przez użytkownika
    client = Socrata("data.cityofchicago.org", "MBVEcIkH7NcG7N4iAvFZ0JAJ4", username="gerus.ewa@gmail.com", password="Hanna930602")
    results = client.get("ijzp-q8t2", where = "year > 2015", district=komenda, limit=100000)
    df = pd.DataFrame.from_records(results)
    
    #ograniczenie wynikow do trzech ostatbich lat
    three_yrs_ago = datetime.now() - relativedelta(years=3)
    df['datetime']=pd.to_datetime(df['date'])
    df=df[df['datetime']> pd.Timestamp(datetime.date(three_yrs_ago))]
    
    #usunięcie zbędnych zmiennych
    cols = [0, 1, 2, 3, 4, 6, 8, 9, 10, 11, 13, 14, 17, 18, 19, 20, 21, 22]
    df.drop(df.columns[cols],axis=1, inplace=True)
    
    #usunięcie z bazy danych obserwacji z brakującymi wynikami
    df.dropna(axis=0, inplace=True)
    
    #duplikacja zmiennej 'date' na potrzeby późniejszych przekształceń 
    df['day']=df['date']
    
    #ekstrakcja ze zmiennej 'date' informacji na temat miesiąca i godziny
    df['month'] = pd.to_datetime(df['date']).dt.month
    df['time'] = pd.to_datetime(df['date']).dt.time
    
    #ekstrakcja ze zmiennej 'date' informacji na temat dnia tygodnia
    df['day'] = pd.to_datetime(df['day']).dt.date
    df['day'] = pd.to_datetime(df['day'])
    df['day']=df['day'].dt.weekday_name
    df=df.drop(['date'], axis=1)
    
    #aplikacja pozostalych filtrów zadanych przez użytkownika
    dzien_tygodnia=list(dzien_tygodnia)
    typ_przestepstwa=list(typ_przestepstwa)
    df=df[df['day'].isin(dzien_tygodnia)]
    df=df[df['month']==miesiac]
    df=df[df['primary_type'].isin(typ_przestepstwa)]
    df=df[df['time']>=godzina_rozpoczecia]
    df=df[df['time']<godzina_zakonczenia]
    
    #implementacja algorytmu K-Średnich
    X=df.loc[:,['latitude','longitude']]
    kmeans = KMeans(n_clusters=liczba_patroli, random_state=0).fit(X)
    labels = kmeans.predict(X)
    df['cluster'] = labels
    
    #zdefiniowanie wyświetlanej tabeli
    b=kmeans.cluster_centers_
    b = pd.DataFrame({'Latitude': b[:, 0], 'Longitude': b[:, 1]})
    b['cluster']=np.arange(len(b))
    def f(row):
        if row['cluster'] == 0:
            return 'czerwony'
        elif row['cluster'] == 1:
            return 'zielony'
        elif row['cluster'] == 2:
            return 'niebieski'
        elif row['cluster'] == 3:
            return 'zolty'
        elif row['cluster'] == 4:
            return 'fioletowy'
        elif row['cluster'] == 5:
            return 'rozowy'
        elif row['cluster'] == 6:
            return 'szary'
        elif row['cluster'] == 7:
            return 'oliwkowy'
        elif row['cluster'] == 8:
            return 'brazowy'
        else:
            return 'bialy'
        return val
    b['kolor'] = b.apply(f, axis=1)
    cols = [2]
    b.drop(b.columns[cols],axis=1, inplace=True)
    
    return b