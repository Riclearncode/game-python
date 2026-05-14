# Pixel Zombie Siege

Game RPG/survival 2D viet bang Python + Pygame. Ban dau nguoi choi co sung luc, giet zombie de nhat vang, sau do dung vang de:

- nang cap sung luc thanh nhieu dong vu khi manh hon;
- dat tru sung tu dong;
- dat hang rao chan co do ben;
- sua cong trinh khi bi zombie tan cong.

AI cua zombie dung thuat toan A* tren ban do o luoi. Zombie se tim duong den nguoi choi, tranh tuong/cong trinh, va tan cong hang rao/tru sung khi bi chan duong.

## Cai dat

```powershell
py -m pip install -r requirements.txt
```

## Chay game

```powershell
py main.py
```

Game se mo o che do full screen va tu can theo do phan giai man hinh hien tai. Man hinh dau tien la menu chinh:

- `Start`: mo man chuan bi tran de chon do kho va nhan vat, sau do bam `Vao tran`.
- `Option`: chinh ngon ngu, am luong nhac/SFX va bat/tat auto fire.
- `Exit`: thoat game.

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
- `F10`: bat/tat Developer Mode de test nhanh
- `P` hoac nut Pause: tam dung game
- Chuot trai khi dang chon cong trinh: dat cong trinh
- Chuot phai hoac `B`: huy che do dat cong trinh
- `R`: sua cong trinh gan nhat
- `Esc`: thoat game

UI moi dat thanh HP/XP o tren man hinh, hotbar nang cap/xay dung o giua phia duoi, va khong con sidebar ben phai de tranh de chu.

Trong `Option` co `Che do nha phat trien`. Khi bat che do nay, vang hien thi `VO HAN`, mua nang cap/dat tru/dat hang rao/sua cong trinh se khong tru vang.

Game co SFX cho nut bam, ban sung, laser, nhat vang, xay dung, nang cap, trung don, no, doc/bile va bat dau wave. Audio dung bo Kenney RPG Audio trong `assets/audio/kenney_rpg`, nguon CC0: https://opengameart.org/content/50-rpg-sound-effects

## He thong zombie

- Walker/Shambler: cham, mau vua, di theo so dong.
- Runner/Infected: nhanh, mau it hon, gay ap luc bat ngo.
- Spitter: khac doc tu xa tao vung AOE gay sat thuong theo thoi gian.
- Boomer: di nhanh hon, co dash, khac dich xanh. Neu trung nguoi choi, zombie se bi kich dong va tang toc manh trong vai giay.
- Boomer khi chet hoac den gan muc tieu se no AOE.
- Stalker: di nhanh, kho thay hon, co cu lao ngan.
- Titan Boss: kich thuoc lon, dung duong di rieng theo kich thuoc than, co the pha cong trinh, charge, stomp, shockwave, goi them zombie va leap/vuot tuong khi bi chan boi dia hinh hep.

Zombie da duoc tang mau, sat thuong va toc do theo wave manh hon ban dau. Tu cac wave sau, chi so zombie tang nhanh hon nguoi choi nen can dung tru sung va hang rao de song sot. Moi wave sau khi clear se co 30 giay nghi de mua/nang cap/dat cong trinh; het gio game tu vao wave tiep theo, hoac bam `Space` de vao ngay.

Do kho anh huong truc tiep den mau, sat thuong, toc do, so luong zombie, vang thuong va sat thuong nguoi choi:

- Easy: de test/choi nhe, zombie yeu hon va roi nhieu vang hon.
- Normal: can bang mac dinh.
- Hard: zombie dong, khoe, nhanh va dau hon.
- Nightmare: zombie scale rat manh, vang it hon, nguoi choi gay sat thuong it hon.

Tru sung va hang rao cung duoc can bang theo do kho. Easy lam cong trinh re/yeu hon mot chut vi zombie khong qua ap luc; Hard va Nightmare tang HP cong trinh, sat thuong/tam ban/toc ban cua tru, dong thoi tang gia nhe de cong trinh dang mua nhung khong the spam vo toi va.

## Level va vu khi

Len level khong chi tang mau. Nguoi choi se nhan cac loi ich that su trong tran:

- tang max HP va hoi mot phan HP;
- tang sat thuong vu khi;
- tang toc ban;
- tang giap giam sat thuong nhan vao;
- tang tam hut vang va bonus vang;
- mo hoi mau cham o cac moc cao.

Nang cap vu khi bang vang se tien hoa theo cac moc:

- Pistol
- Dual Pistols
- SMG
- Shotgun
- Assault Rifle
- Combat Shotgun
- Laser Rifle

Vu khi co gioi han cap toi da la 18. Cap nguoi choi cung bi gioi han de tranh viec nguoi choi manh vuot zombie qua xa. Laser Rifle bay gio ban tia laser that, gay sat thuong theo duong thang va co the xuyen nhieu muc tieu.

Tam ban cua nguoi choi da bi rut ngan de zombie tao ap luc that hon: pistol/SMG phai chien dau gan hon, shotgun la vu khi tam gan, rifle/laser van co loi the tam xa nhung khong con quet gan het ban do.

## Nhan vat

- Soldier: chi so can bang, phu hop mac dinh.
- Scout: chay nhanh, hut vang xa hon, ban nhanh hon nhung mau va damage thap hon.
- Engineer: duoc giam gia xay tru/hang rao/sua chua, co bonus vang nho, hop loi choi phong thu.
- Tank: nhieu mau va giap, damage tot hon, nhung di cham va toc ban kem hon.

## Meo choi

Dung hang rao de lam cham zombie va dat tru sung sau lop chan. Tru sung co the tu dong ban zombie trong tam, nhung ca tru sung va hang rao deu co do ben va co the bi pha.

Khi gap Titan, dung hang rao de cau them thoi gian nhung dung dung yen sau mot lop chan duy nhat: Titan co the dam charge va dap nat cong trinh. Nen vua lui vua dat tru, tranh duong thang khi thay thong bao `Titan charge!`.

Khong nen dua vao hanh lang 1 o de chan Titan nua: Titan co the leap/vuot tuong den khu vuc gan nguoi choi neu bi ket duong.
