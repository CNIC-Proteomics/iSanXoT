import sys
import os
import pandas
import numpy
import re
import dask
import dask.dataframe as dd
from dask.delayed import delayed
from dask.distributed import Client


class builder:
    '''
    Builder class
    '''
    def __init__(self, nworkers, datfile, infiles):
        '''
        Converter builder
        '''
        # number of CPU's
        self.nworkers = nworkers
        # self.client = Client( n_workers=self.nworkers )
        # get the ratios and experiments from the data file
        self.expt, self.ratios = self.infiles_ratios(datfile)
        # create dataframe from the input file(s)
        if isinstance(infiles, str):
            # self.df = pandas.read_csv(infiles, sep="\t", low_memory=False)
            self.ddf = dd.from_delayed( delayed(self._preProcessing)(infiles, self.expt) )
        elif isinstance(infiles, list):
            # d = dd.from_delayed( [delayed(self._preProcessing)(file) for file in infiles] )
            # self.df = d.compute()
            self.ddf = dd.from_delayed( [delayed(self._preProcessing)(file, self.expt) for file in infiles] )

            
    def _preProcessing(self, file, expt):
        '''
        Pre-processing the data: join the files
        '''
        # read input file
        df = pandas.read_csv(file, sep="\t")
        df["Experiment"] = next((x for x in expt if x in file), False)
        return df


    def infiles_ratios(self, ifile):
        '''
        Handles the input data (workflow file)
        '''
        # get the matrix with the ratios
        indata = pandas.read_csv(ifile, usecols=["experiment","ratio_numerator","ratio_denominator"], converters={"experiment":str, "ratio_numerator":str, "ratio_denominator":str})
        ratios = indata.groupby("ratio_denominator")["ratio_numerator"].unique()
        ratios = ratios.reset_index().values.tolist()
        # get the list of sorted experiments discarding empty values
        expt = list( filter(None, indata["experiment"].unique()) )
        expt.sort()
        return expt, ratios


    def infiles_adv(self, ifile):
        '''
        Handles the input data (workflow file)
        '''
        indata = pandas.read_csv(ifile, converters={"experiment":str, "name":str, "ratio_numerator":str, "ratio_denominator":str})
        lblCtr = {}
        # get the list of sorted experiments discarding empty values
        Expt = list( filter(None, indata["experiment"].unique()) )
        Expt.sort()
        # for each row
        for idx, indat in indata.iterrows():
            exp    = indat["experiment"]
            ratio_num = indat["ratio_numerator"]
            ratio_den = indat["ratio_denominator"]
            # ratio numerator and denominator have to be defined
            if not pandas.isnull(exp) and not exp == "" and not pandas.isnull(ratio_num) and not ratio_num == "" and not pandas.isnull(ratio_den) and not ratio_den == "":
                ratio_num = re.sub(r'\n*', '', ratio_num)
                ratio_num = re.sub(r'\s*', '', ratio_num)
                ratio_den = re.sub(r'\n*', '', ratio_den)
                ratio_den = re.sub(r'\s*', '', ratio_den)
                # save for each experiment
                # the means apply to a list of unique tags (num)
                if exp not in lblCtr:
                    lblCtr[exp] = {}
                if ratio_den not in lblCtr[exp]:
                    lblCtr[exp][ratio_den] = []
                if ratio_num not in lblCtr[exp][ratio_den]:
                    lblCtr[exp][ratio_den].append(ratio_num)
        return Expt, lblCtr


    def _calc_ratio(self, df, ControlTag, label):
        '''
        Calculate ratios: Xs, Vs
        '''
        # calculate the mean for the control tags (denominator)
        ct = "-".join(ControlTag)+"_Mean" if len(ControlTag) > 1 else "-".join(ControlTag)
        df[ct] = df[ControlTag].mean(axis=1)
        # calculate the Xs
        Xs = df[label].divide(df[ct], axis=0).applymap(numpy.log2)
        Xs = Xs.add_prefix("Xs_").add_suffix("_vs_"+ct)
        Vs = df[label].gt(df[ct], axis=0)
        # calculate the Vs
        Vs = Vs.mask(Vs==False,df[ct], axis=0).mask(Vs==True, df[label], axis=0)
        Vs = Vs.add_prefix("Vs_").add_suffix("_vs_"+ct)
        #calculate the absolute values for all
        Vab = df[label]
        Vab = Vab.add_prefix("Vs_").add_suffix("_ABS")
        # concatenate all ratios
        df = pandas.concat([df,Xs,Vs,Vab], axis=1)
        return df    

    def _calculate_ratio(self, df, ratios):
        '''
        Calculate the ratios
        '''
        # get the type of ratios we have to do
        for rat in ratios:
            ControlTag = rat[0]
            label = rat[1]
            ControlTag = ControlTag.split(",")
            # create the numerator tags
            labels = []
            for lbl in label:
                # if apply, calculate the mean for the numerator tags (list)
                if ',' in lbl:
                    lbl = lbl.split(",")
                    lb = "-".join(lbl)+"_Mean" if len(lbl) > 1 else "-".join(lbl)
                    df[lb] = df[lbl].mean(axis=1)
                    labels.append( lb )
                else:
                    labels.append( lbl )
            df = self._calc_ratio(df, ControlTag, labels)
        return df

    def calculate_ratio(self):
        '''
        Calculate the ratios
        '''
        # client = Client( n_workers=self.nworkers )
        # self.ddf = self.ddf.set_index('Experiment')
        # Exptr = self.expt + [self.expt[-1]] # I don´t know why but we have to repeat the last experiment in the list for the repartition
        # self.ddf = self.ddf.repartition(divisions=Exptr)
        # # self.ddf = self.ddf.map_partitions(self._calculate_ratio, self.ratios)

        with Client(n_workers=self.nworkers) as client:
            self.ddf = self.ddf.set_index('Experiment')
            Exptr = self.expt + [self.expt[-1]] # I don´t know why but we have to repeat the last experiment in the list for the repartition
            self.ddf = self.ddf.repartition(divisions=Exptr)
            # self.ddf = self.ddf.map_partitions(self._calculate_ratio, self.ratios)
            self.ddf.to_csv( os.path.join(self.outdir,"*/ID-q.tsv"), sep="\t", name_function=self.name)


    def name(self, i):
        self.expt.sort()
        return self.expt[i]

    def to_csv(self, outdir):
        '''
        Print to CSV
        '''
        if self.ddf is not None:
            self.ddf.to_csv( os.path.join(outdir,"*/ID-q.tsv"), sep="\t", name_function=self.name)
            self.client.close()


