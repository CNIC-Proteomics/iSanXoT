# Adaptors

## Under construction

Desribes the scripts.


## SanXoT (integrator)

Checkout the current version from the SVN repository
```bash
svn co svn://aitne.cnic.es/proteomica/integrador/tags/current SanXoT
```

### Convert Python2 to Python3
```bash
cd SanXoT_svn && python3 "c:/Python27/Tools/Scripts/2to3.py" --output-dir=../SanXoT -w -n aljamia.py klibrate.py sanxot.py sanxotsieve.py stats.py

cd ../SanXoT_py3_bak && cp -rp category2all.py p2site.py peptide2all.py peptide2protein.py protein2all.py protein2category.py rels2pq* rels2sp.py scan2peptide.* wf.py ../SanXoT/.

cd ../SanXoT && dos2unix.exe *.py && chmod -x *.py

```


## pRatio

Temporal!!:
For the moment, we extract the columns you need using **aljamia** program:

```bash
set BaseFolder=D:\data\Edema_Oxidation_timecourse_Cys_pig\PTMs
set Data=ID-q_Comet_out_orphans-56_labeled.txt

:: ALJAMIA SData -----------------
aljamia.exe -x"~/test/test_for_corrector/ID-q.txt" -p"" -o"~/test/test_for_corrector/ID-q.Seq-Prot-Redun.txt" -i"[Raw_FirstScan]-[Charge]" -j"[Xs_%%i_126]" -k"[Vs_%%i_126]" -l"PTM" -f"[Modified]== TRUE" -R1
```

## Corrector

Selects the best protein from a list of peptides

