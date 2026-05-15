# Pixel Zombie Siege

Game RPG/survival 2D viet bang Python + Pygame. Ban dau nguoi choi co sung luc, giet zombie de nhat vang, sau do dung vang de:

- nang cap sung luc thanh nhieu dong vu khi manh hon;
- dat tru sung tu dong;
- dat hang rao chan co do ben;
- sua cong trinh khi bi zombie tan cong.

AI cua zombie dung flow-field BFS va A* tren ban do o luoi. Zombie thuong se tim duong den nguoi choi, ton trong tuong/cong trinh, va khi bi chan thi tan cong hang rao/tru sung thay vi di xuyen qua phong tuyen.

## Cai dat

```powershell
py -m pip install -r requirements.txt
```

## Chay game

```powershell
py main.py
```

Game se mo o che do full screen va tu can theo do phan giai man hinh hien tai. Man hinh dau tien la menu chinh:

- `Start`: mo man chuan bi tran de chon do kho, nhan vat va ban do, sau do bam `Vao tran`.
- `Option`: chinh ngon ngu, am luong nhac/SFX va bat/tat auto fire.
- `Exit`: thoat game.

Menu chinh se uu tien dung anh nen `assets/menu_background.png`. Anh duoc scale/crop full man hinh va phu lop toi nhe de chu/nut van de doc.

Kiem tra nhanh khong mo cua so:

```powershell
py main.py --smoke
```

## Dieu khien

- `WASD`: di chuyen
- Chuot trai: ban sung
- `Space`: bat dau dot zombie tiep theo hoac bo qua 30 giay nghi giua wave
- `1`: nang cap vu khi, hoac bam nut 1 o hotbar duoi man hinh
- `2`: chon dat tru sung, hoac bam nut 2 o hotbar
- `3`: chon dat hang rao, hoac bam nut 3 o hotbar
- `F`: bat/tat auto fire
- `Shift`: dash/luot nhanh ngan de ne vong vay
- `I`: bat/tat bang thong tin chi tiet ve nhan vat, vu khi, buff va cong trinh
- `F10`: bat/tat Developer Mode de test nhanh
- `P` hoac nut Pause: tam dung game
- Chuot trai khi dang chon cong trinh: dat cong trinh
- Chuot phai hoac `B`: huy che do dat cong trinh
- `R`: sua cong trinh gan nhat; neu hang rao gan nhat khong bi hong va tech da mo, phim nay se nang cap hang rao
- `Esc`: thoat game

UI moi chi giu HP/XP, vang/wave va hotbar quan trong tren man hinh. Cac chi so chi tiet duoc an trong nut `Chi so`/phim `I`, con hotbar hien truc tiep cooldown dash, auto fire, nang cap va xay dung.

Man hinh chuan bi tran duoc thiet ke lai thanh bo chon co preview: ben trai hien class nhan vat dang chon, ben phai hien mini-map/mau sac map dang chon, o giua la cac nut chon do kho, nhan vat va ban do.

Trong `Option` co `Che do nha phat trien`. Khi bat che do nay, vang hien thi `VO HAN`, mua nang cap/dat tru/dat hang rao/sua cong trinh se khong tru vang, nhung gioi han so tru sung van duoc giu de test can bang.

Game co SFX cho nut bam, ban sung, laser, nhat vang, xay dung, nang cap, trung don, no, doc/bile va bat dau wave. Audio dung bo Kenney RPG Audio trong `assets/audio/kenney_rpg`, nguon CC0: https://opengameart.org/content/50-rpg-sound-effects

Zombie SFX dung them goi OpenGameArt CC0 trong `assets/audio/opengameart`, gom groan/attack/death va Titan roar lay tu Monster Sound Effects Pack. File `assets/audio/SOURCES.md` ghi ro cac nguon Kenney, OpenGameArt, Mixkit va Sonniss; Mixkit/Sonniss duoc de dang mo rong them asset ngoai, nhung khong bundle truc tiep vi goi Sonniss rat lon.

Ngoai ra game co bo audio synth tu tao trong `assets/audio/synth`: tieng sung rieng cho tung vu khi, tieng reload, level-up, nang cap vu khi va 3 track nhac nen cho menu, tran chien va boss. Co the tao lai bo audio nay bang:

```powershell
py tools\generate_synth_audio.py
```

## Tinh nang moi

- Power-up tiep te se xuat hien tren map hoac roi tu zombie Elite: Medkit hoi mau, Overdrive tang damage/toc ban, Shield giam sat thuong, Haste tang toc chay, Shock Core gay no dien quanh nguoi choi.
- Zombie Elite bat dau xuat hien tu wave 3, co vong cam, mau/sat thuong/toc do cao hon, nhung roi vang/XP va co ti le roi power-up tot hon. Elite hien tai manh hon truoc de tao ap luc ro hon o Hard/Nightmare.
- Dash bang `Shift` co cooldown ngan va mot khoanh khac bat tu ngan, dung de cat khoi vong vay hoac thoat doc/bile.
- Nhan vat duoc ve lai theo style concept hero/anime tactical: moi class co silhouette, mau ao giap, vu khi, ao choang/phu kien rieng va animation 4 huong ro rang khi di chuyen/ban sung.
- Tat ca zombie duoc ve lai cung style voi outline dam, mat phat sang, chi tiet rieng cho tung loai va animation theo huong di chuyen.
- Khi vao tran, nguoi choi se duoc teleport vao mot o spawn an toan co khoang trong xung quanh, tranh bi ket trong dia hinh.

## Ban do

Sau khi bam `Start`, nguoi choi co the chon mot trong cac ban do:

- Warehouse/Nha kho: map can bang mac dinh, tong mau kim loai/toi, tuong nha kho, san co crate, ong va dau vet cong nghiep.
- Crossfire Yard/San giao tranh: tong mau dat be-tong nong hon, tuong barricade, vet canh bao va dau vet chien dau.
- Split Ruins/Tan tich chia cat: tong xanh reu, tuong da co, vet nut, co/reu/phien da de tao cam giac tan tich.

## He thong zombie

- Walker/Shambler: cham, mau vua, di theo so dong.
- Runner/Infected: nhanh, mau it hon, gay ap luc bat ngo.
- Spitter: khac doc tu xa tao vung AOE gay sat thuong theo thoi gian.
- Boomer: di nhanh hon, co dash, khac dich xanh. Neu trung nguoi choi, zombie se bi kich dong va tang toc manh trong vai giay.
- Boomer khi chet hoac den gan muc tieu se no AOE.
- Stalker: di nhanh, kho thay hon, co cu lao ngan.
- Titan Boss: kich thuoc lon, dung duong di rieng theo kich thuoc than, co the pha cong trinh, charge, stomp, shockwave, goi them zombie va leap/vuot tuong khi that su bi ket.

AI di chuyen duoc tach chien thuat theo chung loai: Walker dung flow-field BFS chia se de xu ly so dong; Runner dung weighted A* co duong cheo va smoothing de lao nhanh; Spitter tim vi tri giu tam khac doc co line-of-sight; Boomer danh chan vi tri du doan cua nguoi choi; Stalker tim diem flank sau/ben hong va co the vuot hang rao cap thap; Titan dung clearance A* theo ban kinh than, khong di xuyen tuong/hang rao trong di chuyen thuong, va chi leap khi bi ket duong du lau.

Moi loai zombie co theme animation rieng: Runner nghieng nguoi lao nhanh, Spitter co tui doc/phun dich, Boomer co bung doc phat sang, Stalker co ao/bong ma mo, Titan co giap vai, xich va hieu ung khi charge/leap.

Zombie van tang mau, sat thuong va toc do theo wave/do kho, nhung he so scale da duoc ha lai de Nightmare bot qua kho so voi ban buff truoc. Tu cac wave sau, chi so zombie van du ap luc de nguoi choi can dung tru sung va hang rao thay vi chi dua vao vu khi. Moi wave sau khi clear se co 30 giay nghi de mua/nang cap/dat cong trinh; het gio game tu vao wave tiep theo, hoac bam `Space` de vao ngay.

Do kho anh huong truc tiep den mau, sat thuong, toc do, so luong zombie, vang thuong va sat thuong nguoi choi:

- Easy: de test/choi nhe, zombie yeu hon va roi nhieu vang hon.
- Normal: can bang mac dinh.
- Hard: zombie dong, khoe, nhanh va dau hon.
- Nightmare: zombie van rat nguy hiem, vang it hon, nguoi choi gay sat thuong it hon, nhung khong con bi day scale qua cao nhu ban truoc.

Tru sung va hang rao cung duoc can bang theo do kho. Easy lam cong trinh re/yeu hon mot chut vi zombie khong qua ap luc; Hard va Nightmare tang HP cong trinh, sat thuong/tam ban/toc ban cua tru, dong thoi tang gia nhe de cong trinh dang mua nhung khong the spam vo toi va. So tru sung bi gioi han theo do kho: Easy 5, Normal 4, Hard 3, Nightmare 2; Engineer duoc them 1 slot tru.

Hang rao co 5 cap theo tien trinh level/wave: cap cao hon co nhieu HP hon, lam cham zombie khi ap sat, co gai phan sat thuong, cap 4 co mot lan chan Titan charge, va cap 5 co xung dien lam choang zombie nho theo cooldown. Hang rao moi se xay theo cap tech hien tai; hang rao da dat co the nang cap bang `R` khi dung gan.

## Level va vu khi

Len level khong chi tang mau. Nguoi choi se nhan cac loi ich that su trong tran:

- tang max HP va hoi mot phan HP;
- tang sat thuong vu khi;
- tang toc ban;
- tang giap giam sat thuong nhan vao;
- tang tam hut vang va bonus vang;
- mo hoi mau cham o cac moc cao.

Nang cap vu khi bang vang se tien hoa theo cac moc:

- Glock 17: bang 17 vien, nap nhanh, on dinh dau game.
- Dual Beretta 92FS: hai bang 15 vien, moi lan boc coi ton 2 vien.
- HK MP5: bang 30 vien, toc ban cao nhung phai kiem soat reload.
- Mossberg 500: 6 vien dan shotgun, sat thuong gan manh, nap vua phai.
- M4A1 Carbine: bang 30 vien, rifle can bang tam trung/xa.
- Benelli M4: 7 vien shotgun chien dau, clear gan tot nhung khong spam lien tuc.
- XM-LAS Prototype: 6 charge nang luong, xuyen muc tieu manh nhung toc ban cham hon va reload lau hon de tranh qua OP.

Moi tier vu khi co model rieng duoc ve truc tiep tren tay nhan vat: pistol ngan, song luc, SMG, shotgun bom, rifle, shotgun chien dau va sung laser deu co body/nong/bang dan/stock/hieu ung dau nong khac nhau theo dung loai sung.

Tieng ban cung thay doi theo tier vu khi: Glock ngan gon, song Beretta co double-tap, MP5 gat nhanh, shotgun no tram, rifle sac hon va XM-LAS co am laser/sci-fi rieng.

Vu khi co gioi han cap toi da la 18. Cap nguoi choi cung bi gioi han de tranh viec nguoi choi manh vuot zombie qua xa. Tat ca vu khi nay co gioi han bang dan/charge va tu dong nap khi het dan; HUD se hien `Dan x/y` hoac `Dang nap` de nguoi choi can nhac nhip ban.

Tam ban cua nguoi choi da bi rut ngan de zombie tao ap luc that hon: pistol/SMG phai chien dau gan hon, shotgun la vu khi tam gan, rifle/laser van co loi the tam xa nhung khong con quet gan het ban do.

## Nhan vat

- Tat ca class co sprite rieng va animation di chuyen theo 4 huong: xuong, len, trai, phai.
- Soldier: chi so can bang, phu hop mac dinh.
- Scout: chay nhanh, hut vang xa hon, ban nhanh hon nhung mau va damage thap hon.
- Engineer: duoc giam gia xay tru/hang rao/sua chua, co bonus vang nho, hop loi choi phong thu.
- Tank: nhieu mau va giap, damage tot hon, nhung di cham va toc ban kem hon.

## Meo choi

Dung hang rao de lam cham zombie va dat tru sung sau lop chan. Tru sung co the tu dong ban zombie trong tam, nhung ca tru sung va hang rao deu co do ben va co the bi pha.

Khi gap Titan, dung hang rao de cau them thoi gian nhung dung dung yen sau mot lop chan duy nhat: Titan co the dam charge pha mot lop phong tuyen, nhung charge se bi dung/khung khi gap hang rao, dac biet la hang rao cap cao. Nen vua lui vua dat tru, tranh duong thang khi thay thong bao `Titan charge!`.

Khong nen dua vao hanh lang 1 o de chan Titan nua: Titan co the leap/vuot tuong khi bi ket 3-5 giay tuy do kho, nhung diem dap phai cach nguoi choi it nhat 120px, co it nhat hai huong thoat va khong nam trong khu phong thu bi bao kin.
