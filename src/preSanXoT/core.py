import sys
import os
import pandas
import numpy
import re
import dask
from dask.distributed import Client
import dask.dataframe as dd


class builder:
    '''
    Builder class
    '''
    def __init__(self, infile, nworkers):
        '''
        Converter builder
        '''
        self.df = pandas.read_csv(infile, sep="\t", low_memory=False)        

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
        # calculate the mean for the control tags
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

    def calculate_ratio(self, expt, lblCtr):
        '''
        Calculate the ratios
        '''
        # get the name of current experiment
        df = self.df
        for exp in expt:
            if exp in lblCtr:
                for ControlTag,label in lblCtr[exp].items():
                    # create the numerator lists
                    labels = []
                    for lbl in label:
                        if ',' in lbl:
                            lbl = lbl.split(",")
                            lb = "-".join(lbl)+"_Mean" if len(lbl) > 1 else "-".join(lbl)
                            df[lb] = df[lbl].mean(axis=1)
                            labels.append( lb )
                        else:
                            labels.append( lbl )
                    ControlTag = ControlTag.split(",")
                    df = self._calc_ratio(df, ControlTag, labels)
        return df

    def to_csv(self, df, outfile):
        '''
        Print to CSV
        '''
        if df is not None:
            df.to_csv(outfile, sep="\t", index=False)

