# Wedos jako DDNS

Využíval jsem DDNS pro přístup ke svému routeru a dalším zařízením pomocí webové adresy. Po zaplnění DDNS domény ale začal být problém získat SSL certifikát kvůli kvótám na Let's Encrypt. Radši jsem tedy chtěl použít vlastní doménu, kterou jsem si už platil u WEDOSu. To vyžadovalo tvorbu tohodle skriptu. Očekává se použití na Linuxu s init systémem Systemd, určitě se dá adaptovat na Cron, ale já se s tím nezabýval.

### Poznámky

Hodně jsem se inspiroval [tímto php skriptem](http://www.abclinuxu.cz/blog/soban/2016/3/ddns-u-wedosu), jen mě nikdy php nechytlo, tak jsem si napsal něco obdobného v Pythonu.

Skript nepodporuje IPv6. Já ji zatím nepotřebuju, pokud bude zájem, určitě to můžu dopsat.

Momentálně skript umí přepisovat jen prázdný a hvězdičkový záznam ```example.com``` a ```*.example.com```. Je celkem jednoduché ho přimět editovat pouze subdoménový záznam jako např ```raspi.example.com```, stačí v ddns.py dole poupravit cyklus co prochází záznamy.

## Nastavení wedosu
U wedosu je třeba mít zaplé WAPI, wedos má návod jak na to [tady](https://kb.wedos.com/cs/wapi-api-rozhrani/zakladni-informace-wapi-api-rozhrani/wapi-zakladni-informace).


Nutnost vypsat povolené IP adresy je docela gól jelikož přesně to se snažíme pomocí DDNS obejít. Existují ale seznamy rozsahů pro různá ISP. Pokud jste zákazníkem O2 CZ už jsem většinu IP adres sepsal. Nutno dodat, že tento list povoluje i nějaké adresy navíc.

```85.70. 85.71. 83.208. 80.188. 85.70. 88.100. 88.101. 88.102. 88.103. 109.80. 109.81. 194.228. 80.74. 80.188. 90.176. 90.177. 90.178. 90.180. 160.218. 185.61. 194.228. 217.117. 217.194. 37.188. 81.90. 83.69. 92.243.```

Pokud tuto metodu použijete a máte jiného ISP, přidejte mi prosím issue s vaším seznamem IP adres, někomu tím třeba ušetříme čas.

WAPI návod mluví také o IPv6, ale nemá zdokumentované jak nastavit rozsahy. Více k tomuhle v poznámce níž.

## Rozběhnutí skriptu

Skript je nutné spouštět v podsíti, kam chcete mít DNS záznam směrovaný.

Skript vyžaduje Python 3.6 a vyšší
Využívá knihovny requests a requests_toolbelt. Nainstalujete je třeba pomocí

```# pip install -r requirements```
> Jelikož je povolování IPv6 rozsahů na WAPI pro mě nemožné, nutím requests aby použily pro komunikaci s WAPI IPv4 adresu, to rozbije SSL certifikát jelikož čeká webovou adresu, ne IP. V requests_toolbelt existuje HostHeaderSSLAdapter, který pro ověření SSL certifikátu umožní použít HTTP *host* hlavičku namísto adresy požadavku.

Je třeba nastavit tři proměnné prostředí, pokud použijete systemd nenastavujte je
- WAPI_USERNAME - Vaše jméno (emailovka) pro přihlašování k wedosu
- WAPI_PASSWORD - WAPI heslo nastavené při jeho zapínání
- WEDOS_DOMAIN - Jméno vaší domény

Je třeba mít na stroji, kde skript spouštíte nastavený správný čas (stačí snad +- hodina)

Poté by mělo jít skript spustit. ```python ddns.py```

Pro automatické spouštění vyplňte v ddns.service ony tři proměnné prostředí a upravte cesty. Ve výchozím stavu se očekává umístění skriptu v ```/root/ddns/ddns.py```

V ddns.timer můžete upravit časový interval, ve kterém se bude skript spouštět. Poté soubory přesuňte do ```/etc/systemd/system/```.

Pro otestování spusťte

```# systemctl start ddns```

a následně 

```# systemctl status ddns```

Pokud výpis z logu neindikuje chybu, můžete s klidem povolit časovač

```# systemctl enable --now ddns.timer```

## Tipy

Je dobré vyházet IPv6 adresy z WEDOS DNS záznamů, popř. je uklidit někam do subdomény, jinak to lidem s podporou IPv6 bude směrovat jinam.

[Caddy](https://caddyserver.com/docs/automatic-https) umí automaticky žádat o SSL certifikáty všech domén které obhospodařuje. Zároveň je to dobrá http proxy.
