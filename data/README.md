# داده

`quran-uthmani.txt` متن قرآن به رسم عثمانی است، با شمارهٔ سوره و آیه و علائم وقف.

منبع: [Tanzil](https://tanzil.net) — نوع `uthmani` همراه pause marks.

هر خط:

```
شماره‌سوره|شماره‌آیه|متن
```

مثال:

```
2|2|ذَٰلِكَ ٱلْكِتَٰبُ لَا رَيْبَ ۛ فِيهِ ۛ هُدًى لِّلْمُتَّقِينَ
```

جستجو:

```bash
python3 scripts/lookup.py 2 2
python3 scripts/lookup.py بقره 26
```
