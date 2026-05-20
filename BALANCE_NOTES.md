# Pixel Zombie Siege - Balance Notes

## Muc tieu buoc 18

- Kiem tra lai DPS tung vu khi theo progression.
- Giam tinh trang len sung cuoi qua som vi economy qua rong.
- Tang do trau zombie theo mid/late wave de nguoi choi van can xay dung va sua cong trinh.
- Giu sung cuoi manh, nhung khong de Railbreaker pha game.

## Nguyen tac tinh

- `Burst DPS`: sat thuong moi lan bam co chia cho cooldown.
- `Sustained DPS`: DPS co tinh bang dan va reload.
- `Lane Score`: chi so uoc tinh kha nang clear dong, co cong them gia tri pierce/AOE. Day khong phai DPS that 100%, chi dung de so sanh vai tro.
- Shotgun gia dinh tat ca pellet trung muc tieu gan.
- Economy la gia tri trung binh ly thuyet neu nhat het vang.

## Bang vu khi sau can bang

| Tier | Level | Weapon | Unlock gold | Burst DPS | Sustained DPS | Lane score | Vai tro |
|---:|---:|---|---:|---:|---:|---:|---|
| 1 | 1 | Glock 17 | 0 | 63.3 | 52.5 | 52.5 | Sung khoi dau, on dinh |
| 2 | 3 | Dual Beretta 92FS | 280 | 154.5 | 110.9 | 110.9 | Burst dau game, ton dan |
| 3 | 5 | HK MP5 | 782 | 177.8 | 118.5 | 118.5 | SMG clear zombie thuong |
| 4 | 7 | Mossberg 500 | 1493 | 192.9 | 132.0 | 161.0 | Chuyen tri ap sat |
| 5 | 9 | M4A1 Carbine | 2486 | 200.0 | 147.5 | 179.9 | Rifle can bang |
| 6 | 11 | AK-47 | 3771 | 211.4 | 159.7 | 194.8 | Rifle damage cao |
| 7 | 13 | Benelli M4 | 5340 | 436.4 | 303.0 | 436.3 | Shotgun chien dau, gan rat manh |
| 8 | 15 | RPK | 7271 | 365.9 | 261.6 | 261.6 | LMG clear wave lien tuc |
| 9 | 17 | XM-LAS Prototype | 9614 | 270.6 | 167.3 | 424.9 | Laser xuyen hang |
| 10 | 19 | M134 Minigun | 12401 | 444.4 | 305.2 | 305.2 | Crowd control khi thu nha |
| 11 | 21 | Barrett M82A1 | 15770 | 279.6 | 200.0 | 420.0 | Elite/Titan breaker |
| 12 | 23 | XM-Railbreaker | 19821 | 326.0 | 215.9 | 600.2 | Endgame pierce + shock burst |

## Zombie HP tren Normal

| Wave | Walker | Runner | Spitter | Boomer | Stalker | Titan |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 52 | 42 | 76 | 70 | 56 | 520 |
| 3 | 69 | 57 | 103 | 95 | 76 | 765 |
| 5 | 87 | 72 | 131 | 121 | 96 | 1010 |
| 8 | 113 | 96 | 174 | 160 | 128 | 1377 |
| 10 | 134 | 114 | 207 | 191 | 153 | 1646 |
| 12 | 154 | 133 | 241 | 222 | 178 | 1915 |
| 15 | 184 | 162 | 294 | 271 | 216 | 2318 |
| 18 | 218 | 195 | 354 | 326 | 261 | 2755 |
| 20 | 242 | 219 | 397 | 366 | 292 | 3057 |
| 23 | 278 | 256 | 463 | 426 | 341 | 3511 |
| 25 | 302 | 281 | 508 | 468 | 374 | 3813 |

## Economy Normal uoc tinh

| Wave | Enemy count | Wave gold | Cumulative gold |
|---:|---:|---:|---:|
| 1 | 11 | 115.0 | 115.0 |
| 2 | 22 | 229.0 | 344.0 |
| 3 | 30 | 337.0 | 681.0 |
| 4 | 40 | 466.0 | 1147.0 |
| 5 | 49 | 683.5 | 1830.5 |
| 6 | 57 | 723.0 | 2553.5 |
| 7 | 63 | 788.0 | 3341.5 |
| 8 | 71 | 888.0 | 4229.5 |
| 9 | 78 | 1014.0 | 5243.5 |
| 10 | 87 | 1231.5 | 6475.0 |
| 11 | 92 | 1192.0 | 7667.0 |
| 12 | 101 | 1369.0 | 9036.0 |
| 13 | 107 | 1440.0 | 10476.0 |
| 14 | 115 | 1663.0 | 12139.0 |
| 15 | 123 | 1940.5 | 14079.5 |

## Thay doi da ap dung

- Tang chi phi upgrade theo level va tang chi phi mo khoa late-tier.
- Giam spike Benelli M4: van rat manh o tam gan, nhung khong vuot qua RPK/Minigun ve moi tinh huong.
- Buff Barrett M82A1 de dung vai tro diet Elite/Titan ro rang hon.
- Nerf XM-Railbreaker: van la vu khi cuoi tot nhat de clear lane va ban Titan, nhung sustained DPS/AOE khong con qua vo ly.
- Tang HP zombie co ban va dac biet, dac biet tu mid/late wave.
- Titan co base HP cao hon va scale late tot hon.
- Gold drop khong con tang random theo `3 + wave`; thay bang cap gioi han va late bonus nho.
- Elite reward giam nhe tu 1.65x xuong 1.55x.
- Thuong clear wave duoc lam mem lai de economy khong bung qua nhanh.

## Huong test tiep

1. Chay audit:

```powershell
py tools\balance_audit.py
```

2. Chay smoke:

```powershell
py main.py --smoke
```

3. Manual test de can bang cam giac:

- Normal: weapon tier 5-7 nen xuat hien khoang mid game, tier 11-12 khong nen co qua som.
- Hard/Nightmare: hang rao va turret phai co gia tri vi zombie trau hon.
- Benelli M4 phai manh khi zombie ap sat, nhung khong nen thay the moi sung.
- Barrett nen tot voi Elite/Titan nhung yeu hon Minigun/RPK khi bi vay dong.
- Railbreaker nen la endgame reward, manh nhat ve clear lane nhung van bi gioi han bang reload/magazine/cost.
