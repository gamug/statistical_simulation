#This algorith its provisional V 1.1 while solve compatibility problems with scipy and enviroment issues
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as sp
import pandas as pd
import xlwings as xw
import seaborn as sns
import github3 as git
import sys, os, shutil, time, zipfile

def prepare_directory():
    '''''
    Let us prepare model directory where pictures and databases will be place
    '''''
    #Here we configure acces to Qt graphic pluggin for matplotlib
    #path = sys.executable.replace("python.exe", "") + "\\qt.conf"
    #with open(path, "w") as f:
        #f.write("[Paths] \nPrefix = " + sys.executable.replace("python.exe", "").replace("\\", "/") + "Library \n" +
                #"Binaries = " + sys.executable.replace("python.exe", "").replace("\\", "/") + "Library/bin \n" +
                #"Libraries = " + sys.executable.replace("python.exe", "").replace("\\", "/") + "Library/lib \n" +
                #"Headers = " + sys.executable.replace("python.exe", "").replace("\\", "/") + "Library/include/qt \n")
    #f.close()
    wb=xw.Book.caller()
    #Here we upgrade code in case there is a newest version of algorithm
    #And finally we prepare folders to store data and pictures
    path = wb.sheets("xlwings.conf").range("B8").value
    shutil.rmtree(path+r'/Data', ignore_errors=True)
    if not os.path.exists(path+r"\Data"):
        os.makedirs(path+r"\Data")
    if not os.path.exists(path+r"\Graph"):
        os.makedirs(path+r"\Graph")
    if not os.path.exists(path+r"\Runs"):
        os.makedirs(path+r"\Runs")

def upgrade_code():
    try:
        interp_path=sys.executable.replace("python.exe","")
        path=interp_path+'GitHub\\files.zip'
        repo=git.repository('gamug','statistical_simulation')
        repo.archive('zipball',path=path)
        a=zipfile.ZipFile(path,'r')
        with open(interp_path+"GitHub\\upgrated.txt","r") as f:
            upgrated=f.read()
        f.close()
        if str(repo.updated_at)!=upgrated:
            for name in a.namelist():
                if os.path.basename(name)=="statistical_simulation.py":
                    with a.open(name,'r') as f:
                        data=f.read()
                    f.close()
                    with open(interp_path+'statistical_simulation.py','w') as f:
                        f.write(data.decode('utf-8'))
                    f.close()
            with open(interp_path+"GitHub\\upgrated.txt","w") as f:
                f.write(str(repo.updated_at))
            f.close()
    except:
        i=0

def read_distr():
    '''''
    Read the distributions from excel and create a string vector with distributions objects as strings prepared to apply
    eval function.
    
    Return: distributions objects as strings prepared to apply eval function.
    '''''
    wb=xw.Book.caller()
    path = sys.executable.replace("python.exe","distr.txt")
    with open(path, "r") as f:
        dict_distr = eval(f.read())
        f.close()
    value = str(wb.sheets("statistical_simulation").range("E3").value)
    i = 0
    distr = np.empty(0, dtype="str")
    while value != "None":
        s = ""
        for j in range(len(dict_distr[value])):
            s = s + dict_distr[value][j] + str(wb.sheets("statistical_simulation").cells(3 + i, 10 + j).value) + ","
        s = "(" + s[0:len(s) - 1] + ")"
        distr = np.append(distr, "sp." + value + s)
        i = i + 1
        value = str(wb.sheets("statistical_simulation").cells(3 + i, 5).value)
    return distr

def time_delta(deltat):
    '''''
    Transform time second delta into hh/mm/ss format.
    
    delta: Time in seconds.
    
    Return: Time in hh/mm/ss format.
    '''''
    s = (deltat)-((deltat)//60)*60
    if s<10:
        s="0"+str(int(s))
    else:
        s=str(int(s))
    m=(deltat)//60-(((deltat)//60)//60)*60
    if m<10:
        m="0"+str(int(m))
    else:
        m=str(int(m))
    h=(((deltat)//60)//60)
    if h<10:
        h="0"+str(int(h))
    else:
        h=str(int(h))
    t=h+":"+m+":"+s
    return(t)


def couple_model(init, variable, link,name):
    '''''
    Let us couple the model sheets to our model.

    init: Initial row
    variable: Excel's model column where is located the variable names
    link: Excel's model column where is located the variable values.

    Return: None. Couple the excel's python model with a previuos builded and named model.
    '''''
    if name==1:
        aux="uncertainty"
    elif name==2:
        aux="decision"
    wb=xw.Book.caller()
    status=wb.macro("set_statusbar")
    status("Coupling the decision variables...")
    mode = wb.app.calculation
    wb.app.calculation = "manual"
    unnamed=np.empty(0)
    i = -1
    k=0
    condition = True
    while condition:
        i = i + 1
        if wb.sheets("statistical_simulation").cells(init + i, variable).value!= None:
            cell = wb.sheets("statistical_simulation").cells(init + i, link).address
            for sheet in wb.sheets:
                try:
                    wb.sheets(sheet).range(wb.sheets("statistical_simulation").cells(init + i,
                                                                                     variable).value).value = "=statistical_simulation!" + cell
                    k=1
                    break
                except:
                    continue
            if k==0:
                unnamed=np.append(unnamed,wb.sheets("statistical_simulation").cells(init + i, variable).value)
            k=0
        else:
            condition = False
    wb.app.calculation = mode
    vari=""
    if len(unnamed)!=0:
        for var in unnamed:
            vari=var+", "+vari
        raise Exception("UnnamedVariables: following "+aux+ " variables aren't named in model: "+vari[0:len(vari)-2])

def couple_answers():
    wb = xw.Book.caller()
    status = wb.macro("set_statusbar")
    status("Coupling the answers variables...")
    mode = wb.app.calculation
    wb.app.calculation = "manual"
    i=0
    while wb.sheets("answers").cells(1+i,1).value!=None:
        for sheet in wb.sheets:
            try:
                a=wb.sheets(sheet).range(wb.sheets("answers").cells(1+i,1).value).value
                wb.sheets("answers").cells(1+i,2).value=sheet.name
                break
            except:
                continue
        i=i+1
    wb.app.calculation = mode
    status("The model was coupled")

def copy_dabase():
    '''''
    Make a copy of the databases in Runs model directory
    '''''
    wb = xw.Book.caller()
    path = wb.sheets("xlwings.conf").range("B8").value
    name=str(wb.sheets("statistical_simulation").range("B6").value)
    try:
        shutil.copytree(path+r"\Data", path+r"\Runs\copy_"+name)
        with open(path+r"\Runs\copy_"+name+r"\readme.txt","w") as f:
            f.write(wb.sheets("statistical_simulation").range("B9").value)
        f.close()
    except:
        a=True
        i=0
        while a:
            i=i+1
            try:
                shutil.copytree(path+r"\Data", path+r"\Runs\copy_"+str(i)+"_"+name)
                with open(path + r"\Runs\copy_" + str(i)+"_"+name + r"\readme.txt", "w") as f:
                    f.write(wb.sheets("statistical_simulation").range("B9").value)
                f.close()
                break
            except:
                continue


#AN USEFULL FUNCTION USED IN CLASS FIELD __INIT__
def find_between(s,first,last):
    '''''
    This internal calculation function let us extract string characters between two symbols.
    
    s: Initial string characters.
    first: Left symbol between which we extract.
    last: Right symbol between which we extract.
    
    Return: String character between first and last
    '''''
    try:
        start=s.index(first)+len(first)
        end=s.index(last,start)
        return s[start:end]
    except ValueError:
        return ""

# CLASS ANSWERS FROM MODEL
class field:
    '''''
    Class that let us managing answers information to initial storage and to generate database.
    
    path: Path where is located model.
    sheet: Sheet in the model where is located the answer's variables list. Variables list must be located in the first 
           column, first row. You can put it by tipping "F3" and selecting the desired variable to output in database.
    sep: Symbol used to extract the variable name. You must take care about how you write the symbols to read variable 
         names.
    
    Return: Object with desired characteristics to read and write answer variables
    '''''
    def __init__(self, path, sheet="answers", sep="'"):
        wb = xw.Book.caller()
        self.path =  wb.sheets("xlwings.conf").range("B8").value
        self.sheet = sheet
        self.answers = {}
        self.results = {}
        self.vectors = {}
        self.a = np.empty(0)
        a1 = np.array(wb.sheets("answers").range("A1:A5000").value, dtype="str")
        a1 = a1[np.where(a1 != "None")]
        a2 = np.array(wb.sheets("answers").range("B1:B" + str(len(a1))).value, dtype="str")
        self.a = [a1, a2]

    def save_iteration(self, itera):
        '''''
        Class method used to save iteration "itera" in a provisional database.
        
        itera: Number of iteration.
        
        Return: None. Storage the data in "self.answers" dictionary.
        '''''
        wb = xw.Book.caller()
        for i in range(len(self.a[0])):
            if itera == 0:
                self.answers[self.a[0][i]] = [wb.sheets(self.a[1][i]).range(self.a[0][i]).value]
            else:
                self.answers[self.a[0][i]] = np.append(self.answers[self.a[0][i]],
                                                       [wb.sheets(self.a[1][i]).range(self.a[0][i]).value], axis=0)

    def save_data(self,mode="w",header=True):
        wb = xw.Book.caller()
        dec = np.array(wb.sheets("statistical_simulation").range("UA2:UA5000").value, dtype="str")
        dec = np.delete(dec, np.where(dec == "None"))
        perc = np.array(eval(wb.sheets("statistical_simulation").range("B8").value), dtype="float")
        for variable in self.a[0]:
            if not variable[0] == "V":
                self.results[variable] = self.answers[variable]
            else:
                aux = pd.DataFrame.from_dict(self.answers[variable])
                aux.to_csv(self.path + r"\Data" + r"\Vector" + variable[1:len(variable)] + r".csv",mode=mode,header=header)
        if wb.sheets("statistical_simulation").range("B4").value=="Yes":
            calcule_percentil(pd.DataFrame.from_dict(self.results),perc,dec).to_csv(self.path + r"\Data\economics.csv",mode=mode,header=header)
        else:
            pd.DataFrame.from_dict(self.results).to_csv(self.path + r"\Data\economics.csv",mode=mode,header=header)
    def read_data(self):
        '''''
        Class method used to read data previously saved in "Data" folder inside the "path" directory.
        
        Return: None. It place database results in "self.results" class property.
        '''''
        wb = xw.Book.caller()
        for variable in self.a[0]:
            if variable[0] == "V":
                self.vectors[variable] = pd.read_csv(
                    self.path + r"\Data" + "\Vector" + variable[1:len(variable)] + r".csv", header=0, index_col=0)
                self.results=pd.read_csv(self.path + r"\Data\economics.csv", header=0)

#AN USEFULL FUNCTION
def distr_run(q,distri,method):
    '''''
    Function that let us transform string character (representing a statistical frozen distribution) in a real
    statistical frozen distribution.
    
    q: Vector where is place the data to transform (percentile, random variates, etc).
    distri: String character representing a statistical frozen distribution.
    method: One of the scipy.stats distribution methods available to transform q ("ppf", "cdf", "pdf", etc).
    
    Return: Transformed matrix q.
    '''''
    function=distri+"."+method+"(q)"
    samples=eval(function)
    return samples

#THIS FUNCTION LET AS CALCULATE INCERTIDUMBRE VECTOR FOR MONTECARLO RUNING
def montecarlo():
    '''''
    Realize sampling taking in account model settled variables for montecarlo sampling rule.
    
    Return: Sampled uncertainty variables.
    '''''
    wb = xw.Book.caller()
    wb.app.calculate()
    var_names=np.array(wb.sheets("statistical_simulation").range("C3:C1000").value,dtype="str")
    var_names=np.delete(var_names,np.where(var_names=="None"))
    var_names1=var_names
    distr=read_distr()
    corr_value=np.array(wb.sheets("statistical_simulation").range("G3:G"+str(len(var_names)+2)).value,dtype="str")
    corr_value=np.delete(corr_value,np.where(corr_value=="None"))
    corr_names=np.array(wb.sheets("statistical_simulation").range("F3:F"+str(len(var_names)+2)).value,dtype="str")
    corr_names1=np.delete(corr_names,np.where(corr_names=="None"))
    corr_names2=corr_names1
    truncate={}
    for i in range(len(var_names)):
        if not wb.sheets("statistical_simulation").cells(3+i,8).value==None or not wb.sheets("statistical_simulation").cells(3+i,9).value==None:
            truncate[var_names[i]]=np.array([0 if wb.sheets("statistical_simulation").cells(3+i,8).value==None else distr_run(wb.sheets("statistical_simulation").cells(3+i,8).value,distr[i],"cdf"),
                                            1 if wb.sheets("statistical_simulation").cells(3+i,9).value==None else distr_run(wb.sheets("statistical_simulation").cells(3+i,9).value,distr[i],"cdf")])
    incert=int(wb.sheets("statistical_simulation").range("B1").value)
    incert_var={}
    for var in var_names:
        incert_var[var]=np.empty(0)
    var=0
    #Correlating variables
    while not len(corr_names2)==0:
        a=np.where(corr_names1==corr_names2[0])[0]
        aux=np.empty((len(a)+1,len(a)+1))
        for i in range(len(a)+1):
            for j in range(len(a)+1):
                if j==i:
                    aux[i][j]=1
                elif j<i:
                    aux[i][j]=corr_value[a[j]]
                else:
                    aux[i][j]=corr_value[a[j-1]]
        aux=sp.multivariate_normal.rvs(cov=aux,size=incert)
        incert_var[corr_names2[0]]=distr_run(sp.norm.cdf(aux[:,0]),distr[np.where(var_names==corr_names2[0])[0][0]],"ppf")
        var_names1=np.delete(var_names1,np.where(var_names1==corr_names2[0]))
        for i in range(len(a)):
            var=var_names[np.where(corr_names==corr_names1[a[i]])[0][i]]
            incert_var[var]=distr_run(sp.norm.cdf(aux[:,i+1]),distr[np.where(var_names==var)[0][0]],"ppf")
            var_names1=np.delete(var_names1,np.where(var_names1==var))
        corr_names2=np.delete(corr_names2,np.where(corr_names2==corr_names2[0]))
        aux=""
    #Generating non correlated variables
    for var in var_names1:
        aux=sp.norm.cdf(sp.norm.rvs(size=incert))
        incert_var[var]=distr_run(aux,distr[np.where(var_names==var)[0][0]],"ppf")
    #Finally, truncate variables
    for var in truncate:
        tr_inf=truncate[var][0]
        tr_sup=truncate[var][1]
        aux=distr_run(incert_var[var],distr[np.where(var_names==var)][0],"cdf")
        aux=(tr_sup-tr_inf)*aux+tr_inf
        incert_var[var]=distr_run(aux,distr[np.where(var_names==var)][0],"ppf")
    #Now we return the incertidumbre vector
    for var in var_names:
        i=i+1
        incerti[:,i] = incert_var[var]
    return incerti

def sort_population(l, criteria):
    '''''
    Sort the population in olhs genetic algorith

    l: Initial population.
    criteria: Sorting population criterion. "md" for maximun distance value and "force" for force criterion value

    Return: Positional matrix that makes l sort in growing order, criterial value for the l matrix.
    '''''
    if criteria == 'md':
        crit_value = np.array([d(l['l' + str(i + 1)]) for i in range(8)])
        crit_value = np.array(
            [np.linspace(1, 8, 8), [crit_value[i][0] for i in range(8)], [crit_value[i][1] for i in range(8)]])
        order = np.lexsort((crit_value[0], crit_value[1]))
    else:
        crit_value = np.array([np.linspace(1, 8, 8), [g(l['l' + str(i + 1)]) for i in range(8)]])
        order = np.lexsort((crit_value[0], crit_value[1]))
    return [order, crit_value[1]]

def mutate_population(l, order):
    '''''
    Mutate population in olhs genetic algorithm

    l: Initial population to mutate.
    order: Criterion order for initial population.

    Return: Mutated population
    '''''
    l2 = {}
    l2['l1'] = l['l' + str(order[0] + 1)]
    l2['l5'] = l['l' + str(order[0] + 1)]
    a = np.random.randint(0, len(l['l1'][0] - 1))
    b = np.random.randint(0, len(l['l1'][0] - 1))
    aux1 = l2['l5'][:, a]
    aux2 = l2['l5'][:, b]
    l2['l5'][:, a] = aux2
    l2['l5'][:, b] = aux1
    for i in range(3):
        a = np.random.randint(0, len(l['l1'][0] - 1))
        b = np.random.randint(0, len(l['l1'][0] - 1))
        l2['l' + str(i + 2)] = l['l' + str(order[0] + 1)]
        l2['l' + str(i + 6)] = l['l' + str(order[i + 1] + 1)]
        l2['l' + str(i + 2)][:, a] = l['l' + str(order[i + 1] + 1)][:, a]
        l2['l' + str(i + 6)][:, b] = l['l' + str(order[0] + 1)][:, b]
    return l2

def d(lse):
    '''''
    Calculate distance criterion value for the lse matrix pased.

    lse: matrix with n numbers of uncertainties with p variations.

    Return: Distance criteria for each uncertainty variable.
    '''''
    aux = np.empty(0)
    for i in range(len(lse)):
        for j in range(len(lse)):
            if not j == i:
                aux1 = np.power(np.linalg.norm(lse[i] - lse[j]), 2)
                aux = np.append(aux, aux1)
    return np.array([min(aux), len(aux[np.where(aux == min(aux))])])

def g(lse):
    '''''
    Calculate force criterion value for the lse matrix pased.

    lse: matrix with n numbers of uncertainties with p variations.

    Return: Force criteria for each uncertainty variable.
    '''''
    aux = 0
    for i in range(len(lse)):
        for j in range(i + 1, len(lse)):
            aux = aux + 1 / np.power(np.linalg.norm(lse[i] - lse[j]), 2)
        return aux

def lhs(n):
    '''''
    LHS: Lating Hypercube Sampling for a single uncertainty variable.

    n: Number of variations for a variable sampled

    Return: Percentiles for a sampled variable.
    '''''
    samples = np.array([i / n + (1 / n) / 2 for i in range(n)])
    return samples

def rlhs(n, p,seed=123456):
    '''''
    RLHS: Random Latin-Hypercube Sampling.

    p: Number of uncertainties consider in sampling.
    n: Number of samples per uncertainty variable.
    seed: Seed to define RandomState.

    Return: Percentiles for each sampled variables
    '''''
    state=np.random.RandomState(seed=seed)
    seeds=state.randint(0,1000000000,size=p)
    var_samples = np.empty((n, p))
    samples = lhs(n)
    for i in range(p):
        state=np.random.RandomState(seed=seeds[i])
        aux = samples
        state.shuffle(aux)
        var_samples[:, i] = aux
    return var_samples

def olhs(n, p, criteria="force", g=False):
    '''''
    OLHS: Optimal Latin-Hypercube Sampling.
    This method try to generate a sampling with a good espacing between each multiparameter sampling.

    p: Number of uncertainties consider in sampling.
    n: Number of samples per uncertainty variable.
    criteria: Sorting population criterion. "md" for maximun distance value and "force" for force criterion value
    g: If True return an internal calculated optimized value.

    Return: Percentiles for each sampled variables
    '''''
    # seting initial population
    l1 = {}
    for j in range(8):
        aux = rlhs(n, p)
        l1['l' + str(j + 1)] = aux
    # sorting initial population
    order1 = np.array([sort_population(l1, criteria)[0][i] for i in range(4)])
    crit_value0 = sort_population(l1, criteria)[1][order1[0]]
    crit_value_best = crit_value0
    crit_value_nk = crit_value0
    lbest = l1['l' + str(order1[0] + 1)]
    crit = True
    i = 0
    epsilon = 1e-7
    m = 50
    while crit:
        i = i + 1
        # mutating population
        l1 = mutate_population(l1, order1)
        # sorting population
        crit_value1 = sort_population(l1, criteria)
        order1 = np.array([crit_value1[0][i] for i in range(4)])
        crit_value1 = crit_value1[1][order1[0]]
        if i % m == 0:
            gn = crit_value1 - crit_value0
            gk = crit_value_best - crit_value_nk
            if gk < epsilon * gn:
                crit = False
            crit_value_nk = crit_value1
        if crit_value_best < crit_value1 or i>80000:
            crit_value_best = crit_value1
            lbest = l1['l' + str(order1[0] + 1)]
    if g == False:
        return lbest
    else:
        return np.array([lbest, crit_value_best])

# AND YOU CAN CORRELATE VARIABLES TOO
def distr_fromrvs(rvs, bins=10):
    '''''
    Generate a interval histogram for a sampled correlated variable that let us read a percentile correlated variation.

    rvs: Multivariate normal random variates.
    bins: Number of bins in histogram

    Return: Correlated percentile for each rvs passed
    '''''
    cdf = np.empty((2, bins))
    aux = np.histogram(rvs, bins=bins)
    aux = [aux[0] / len(rvs), aux[1][0:bins]]
    cdf[1] = aux[1]
    cdf[0][0] = aux[0][0]
    for i in range(bins):
        if i > 0:
            cdf[0][i] = aux[0][i] + cdf[0][i - 1]
    return cdf

def ppf(x, cdf):
    '''''
    Generate a correlated random variate (standard normal distribution).

    x: Value to correlate.
    cdf: Correlated percentile.

    Return: Random variate correlated
    '''''
    cond = True;
    n = 1;
    while cond:
        xi = cdf[1][np.where((cdf[0] > x - n / (2 * len(cdf[0]))) & (cdf[0] < x + n / (2 * len(cdf[0]))))]
        if len(xi) > 1:
            return np.average(xi)
            cond = False
        n = n + 1

def correlate(perc, corrcoef):
    '''''
    Correlate a variable with another pre-existent one.

    perc: Percentile of a pre-existent variable
    corrcoef: Correlation coefficient between the two variables.

    Return: Correlated variables.
    '''''
    aux = sp.multivariate_normal.rvs(cov=[[1, corrcoef], [corrcoef, 1]], size=1000000)
    aux[:, 1] = sp.norm.cdf(aux[:, 1])
    result = np.empty(len(perc))
    # lets iterate along perc
    for i in range(len(perc)):
        try:
            xi = aux[:, 0][
                np.where((aux[:, 1] > perc[i] - 1 / (2 * len(perc))) & (aux[:, 1] < perc[i] + 1 / (2 * len(perc))))]
            cdf = distr_fromrvs(xi, bins=50)
            result[i] = ppf(np.random.uniform(1 / (2 * len(perc)), 1 - 1 / (2 * len(perc))), cdf)
            result[i] = ppf(np.random.uniform(1 / (len(perc)), 1 - 1 / (len(perc))), cdf)
        except:
            xi = aux[:, 0][np.where((aux[:, 1] > perc[i] - 1 / (len(perc))) & (aux[:, 1] < perc[i] + 1 / (len(perc))))]
            cdf = distr_fromrvs(xi, bins=50)
            result[i] = ppf(np.random.uniform(1 / (2 * len(perc)), 1 - 1 / (2 * len(perc))), cdf)
            result[i] = ppf(np.random.uniform(1 / (len(perc)), 1 - 1 / (len(perc))), cdf)
    return result

def run_lhs():
    '''''
    Realize sampling taking in account model settled variables for Latin-Hypercube sampling rule.

    Return: Sampled uncertainty variables.
    '''''
    wb = xw.Book.caller()
    wb.app.calculate()
    seed=int(wb.sheets("statistical_simulation").range("B7").value)
    var_names = np.array(wb.sheets("statistical_simulation").range("C3:C5000").value, dtype="str")
    var_names = np.delete(var_names, np.where(var_names == "None"))
    distr = read_distr()
    corr_value = np.array(wb.sheets("statistical_simulation").range("G3:G" + str(len(var_names) + 2)).value,
                          dtype="str")
    corr_names = np.array(wb.sheets("statistical_simulation").range("F3:F" + str(len(var_names) + 2)).value,
                          dtype="str")
    corr_names1 = np.unique(np.delete(corr_names, np.where(corr_names == "None")))
    noncorr_names = var_names
    aux = corr_names
    for var in corr_names1:
        noncorr_names = np.delete(noncorr_names, np.where(aux == var))
        aux = np.delete(aux, np.where(aux == var))
    incert = int(wb.sheets("statistical_simulation").range("B1").value)
    truncate = {}
    for i in range(len(var_names)):
        if not wb.sheets("statistical_simulation").cells(3 + i, 8).value == None or not wb.sheets(
                "statistical_simulation").cells(3 + i, 9).value == None:
            try:
                truncate[var_names[i]] = np.array([0 if wb.sheets("statistical_simulation").cells(3 + i,
                                                                                                  8).value == None else distr_run(
                    wb.sheets("statistical_simulation").cells(3 + i, 8).value, distr[i], "cdf"),
                                                   1 if wb.sheets("statistical_simulation").cells(3 + i,
                                                                                                  9).value == None else distr_run(
                                                       wb.sheets("statistical_simulation").cells(3 + i, 9).value, distr[i],
                                                       "cdf")])
            except:
                raise Exception("TruncateError: there is a problem with " + var_names[i] + " uncertainty variable")
    incert_var = {}
    for var in var_names:
        incert_var[var] = np.empty(0)
    # Generating non-correlated samples
    if wb.sheets("statistical_simulation").range("B2").value == "RLHS":
        samples = rlhs(incert, len(noncorr_names),seed)
    else:
        samples = olhs(incert, len(noncorr_names), "force")
    i=-1
    for var in noncorr_names:
        try:
            i = i + 1
            incert_var[var] = samples[:, i]
        except:
            raise Exception("DistributionError: there is a problem with "+var+" uncertainty variable")
    # In this step we correlate the variables (in case we have)
    distr_names = np.array(wb.sheets("statistical_simulation").range("C3:C5000").value, dtype="str")
    distr_names = np.delete(distr_names, np.where(distr_names == "None"))
    distr_names
    warning = np.empty(0, dtype="str")
    for i in range(len(distr_names)):
        if str(wb.sheets("statistical_simulation").cells(3 + i, 6).value) != "None":
            for j in range(len(distr_names)):
                if wb.sheets("statistical_simulation").cells(3 + i, 3).value == wb.sheets(
                        "statistical_simulation").cells(3 + j, 6).value:
                    warning = np.append(warning, wb.sheets("statistical_simulation").cells(3 + i, 3).value)
    warning = np.unique(warning)
    if len(warning) > 0:
        s = ""
        for i in warning:
            s = s + i + ", "
        raise Exception(
            "CorrelateError: variable can't be correlate and correlated at the same time, please check " + s[0:len(
                s) - 2] + " uncertainty variables")
        return
    for var in corr_names1:
        try:
            for corr in np.where(corr_names == var)[0]:
                corrcoef = corr_value[corr]
                perc = incert_var[corr_names[corr]]
                #incert_var[var_names[corr]] = distr_run(correlate(perc, corrcoef),
                                                        #distr[np.where(var_names == var)][0], "cdf")
                incert_var[var_names[corr]] = sp.norm.cdf(correlate(perc, corrcoef))
        except:
            raise Exception("CorrelateError: there is a problem with " + var + " uncertainty variable")
    #We must truncate variables in case we have
    for var in truncate:
        try:
            tr_inf = truncate[var][0]
            tr_sup = truncate[var][1]
            aux = incert_var[var]
            aux = (tr_sup - tr_inf) * aux + tr_inf
            incert_var[var] = aux
        except:
            raise Exception("TruncateError: there is a problem with "+var+" uncertainty variable")
    for var in var_names:
        try:
            incert_var[var] = distr_run(incert_var[var], distr[np.where(var_names == var)][0], "ppf")
        except:
            raise Exception("DistributionError: there is a problem with " + var + " uncertainty variable")
    incerti = np.empty([incert, len(var_names)])
    i=-1
    for var in var_names:
        try:
            i = i + 1
            incerti[:, i] = incert_var[var]
        except:
            raise Exception("DistributionError: there is a problem with " + var + " uncertainty variable")
    return incerti

def dec_allvar():
    '''''
    Generate all decision combination for the model variables defined

    Return: i-th decision combination using a generator and number of combinations.
    '''''
    wb=xw.Book.caller()
    wb.app.calculate()
    dec_names = np.array(wb.sheets("statistical_simulation").range("UA2:UA5000").value, dtype="str")
    dec_names = np.delete(dec_names, np.where(dec_names == "None"))
    if len(dec_names)>1:
        dec_var = np.array(wb.sheets("statistical_simulation").range("UB2:UB" + str(len(dec_names) + 1)).value, dtype=str)
    else:
        dec_var=wb.sheets("statistical_simulation").range("UB2").value
    try:
        dec_var1 = np.array([np.array(eval(dec_vari), dtype="int") for dec_vari in dec_var])
    except:
        try:
            dec_var1=np.array([np.array(eval(dec_var),dtype="int")])
        except:
            raise Exception("DecisionError: there is a problem with one or more decisions variables")
    dec_var=dec_var1
    comb = 1
    dec_value = np.empty(0)
    dec_index = np.zeros(len(dec_var))
    dec_comb = np.empty(len(dec_names))
    dec_index[len(dec_var) - 1] = -1
    for var in dec_var:
        try:
            comb = comb * len(var)
            dec_value = np.append(dec_value, var[0])
        except:
            raise Exception("DecisionError: there is a problem with " + var + " decision variable")
    for i in range(comb):
        k = len(dec_var) - 1
        dec_index[k] = dec_index[k] + 1
        z = 0
        while dec_index[k] > len(dec_var[k]) - 1:
            dec_index[k] = 0
            k = k - 1
            dec_index[k] = dec_index[k] + 1
        # yield dec_index
        for i in range(len(dec_names)):
            dec_comb[i] = dec_var[i][int(dec_index[i])]
        yield [dec_comb, comb]

def calcule_percentil(df,perc,dec):
    '''''
    let us calculate percentiles from a iteration.
    df: DataFrame to be processed.
    perc: Percentiles for calculations.
    dec: Decision labels of the model.
    Return: df with percentiles.
    '''''
    aux=df.drop(dec,axis=1)
    labels=np.empty(0)
    perc=np.array(perc,dtype="float")
    for value in perc:
        labels=np.append(labels,aux.axes[1]+"_P"+str(int(value)))
    i=-1
    j=-1
    for value in labels:
        i=i+1
        if i%len(aux.axes[1])==0:
            j=j+1
            i=0
        df[value]=np.percentile(np.array(df[aux.axes[1][i]],dtype="float"),perc[j])
    return df

#MAIN RUNNING ALGORITHM
def run():
    ''''' 
    Mean algorithm. Read running the data and let us simulate specific model with specific features.
    '''''
    wb = xw.Book.caller()
    path = wb.sheets("xlwings.conf").range("B8").value
    modexl = wb.app.calculation
    wb.app.calculation = "manual"
    wb.app.calculate()
    status=wb.macro("set_statusbar")
    status("Preparing working directory...")
    prepare_directory()
    incert=int(wb.sheets("statistical_simulation").range("B1").value)
    data=field(path)
    wb.sheets("statistical_simulation").range("P3:P5000").clear_contents()
    #Here we sample the uncertainty variables
    if not wb.sheets("statistical_simulation").range("B3").value=="Decision":
        status("Sampling variables...")
        if wb.sheets("statistical_simulation").range("B2").value=="Montecarlo":
            samples=montecarlo()
        else:
            samples=run_lhs()
    #And generate decision combinations
    status("Turning on the blender...")
    if wb.sheets("statistical_simulation").range("B3").value=="Decision":
        dec_var=dec_allvar()
    #Finally, we iterate along the data we have
    ti=time.time()
    titer=ti
    t=np.empty(0)
    if wb.sheets("statistical_simulation").range("B3").value == "Decision":
        dec_var=dec_allvar()
        comb=next(dec_var)[1]
        dec_var=dec_allvar()
        for itera in range(comb):
            t = np.append(t, time.time() - titer)
            titer = time.time()
            wb.sheets("statistical_simulation").range("UC2").options(transpose=True).value=next(dec_var)[0]
            status("Iteration " + str(itera + 1) + " from " + str(comb) + "  -----  " + str(
                round((itera + 1) * 100 / comb, 1)) + "% advance ----- Elapsed time "+time_delta(time.time()-ti)+
                   " ----- Remaining time "+time_delta(np.average(t)*comb-(time.time()-ti)))
            data.save_iteration(itera)
        data.save_data()
    elif wb.sheets("statistical_simulation").range("B3").value == "Uncertainty":
        for itera in range(incert):
            t=np.append(t,time.time()-titer)
            titer=time.time()
            wb.sheets("statistical_simulation").range("P3").options(transpose=True).value = samples[itera]
            wb.app.calculate()
            status("Iteration " + str(itera + 1) + " from " + str(incert) + "  -----  " + str(
                round((itera + 1) * 100 / incert, 1)) + "% advance ----- Elapsed time "+time_delta(time.time()-ti)+
                   " ----- Remaining time "+time_delta(np.average(t)*incert-(time.time()-ti)))
            data.save_iteration(itera)
        data.save_data()
    else:
        dec_var = dec_allvar()
        comb=next(dec_var)[1]
        dec_var=dec_allvar()
        k=0
        for dec in range(comb):
            wb.sheets("statistical_simulation").range("UC2").options(transpose=True).value = next(dec_var)[0]
            for itera in range(incert):
                t = np.append(t, time.time() - titer)
                titer = time.time()
                k=k+1
                wb.sheets("statistical_simulation").range("P3").options(transpose=True).value = samples[itera]
                wb.app.calculate()
                status("Iteration " + str(k) + " from " + str(incert*comb) + "  -----  " + str(
                    round((k) * 100 / (incert*comb), 1)) + "% advance ----- Elapsed time "+time_delta(time.time()-ti)+
                       " ----- Remaining time "+time_delta(np.average(t)*incert*comb-(time.time()-ti)))
                data.save_iteration(itera)
            if k==incert:
                data.save_data()
            else:
                data.save_data(mode="a",header=False)
    if wb.sheets("statistical_simulation").range("B5").value=="Yes":
        status("Copying your data...")
        copy_dabase()
    wb.app.calculation=modexl
    status("Done")

#LET AS PLOTING HISTOGRAM AND FIT DISTRIBUTIONS
def plot_hist_ies(wb):
    '''''
    This function plot a single histogram.
    '''''
    #Preparing everithing we need to plot
    path = wb.sheets("xlwings.conf").range("B8").value
    s=""
    with open(sys.executable.replace("python.exe","distr.txt"),"r") as f:
        distr=eval(f.read())
    wb.app.calculate()
    variable_name=wb.sheets("distr_lab").range("F3").value
    path_p=os.path.join(path,"graph","histograms_"+wb.sheets("distr_lab").range("F2").value)
    #There we create plots repository
    if not os.path.exists(path_p):
        os.makedirs(path_p)
    #First, clean graph zone
    try:
        wb.sheets("distr_lab").pictures("fig1").delete()
    except:
        pass
        #Now we must read features
    bins=int(wb.sheets("distr_lab").range("F4").value)
    save_pict=wb.sheets("distr_lab").range("F1").value
    fit_distri=wb.sheets("distr_lab").range("F5").value
    perc=wb.sheets("distr_lab").range("F9").value
        #Then lets read the data
    aux=wb.sheets("distr_lab").range("a3:a100000").value
    i=-1
    data=np.array(wb.sheets("distr_lab").range("A3:A5000").value,dtype=str)
    data=np.delete(data,np.where(data=="None"))
    data=data.astype(float)
        #And, finally, plot the data histogram
    mpl_fig=plt.Figure(figsize=(5.3,3))
    ax=mpl_fig.add_subplot(111)
            #If user wanna fit the distribution
    if fit_distri=="Yes":
        if "loc=" in distr[wb.sheets("distr_lab").range("F7").value] and not wb.sheets("distr_lab").range("F8").value=="True":
            s="sp."+wb.sheets("distr_lab").range("F7").value+".fit(data)"
        else:
            s="sp."+wb.sheets("distr_lab").range("F7").value+".fit(data,floc=0)"
        fit_distr=eval(s)
        i=-1
        text=""
        for value in fit_distr:
            i=i+1
            text=text+distr[wb.sheets("distr_lab").range("F7").value][i]+str(round(value,3))+"\n"
        y=max(np.histogram(data,bins=bins,density=True)[0])
        x=max(data)
        ax.text(0.6*x,0.7*y,s=text,fontsize=8)
        sns.distplot(data,bins=bins,kde=False,fit=eval("sp."+wb.sheets("distr_lab").range("F7").value),ax=ax)
        s="_distr_"+wb.sheets("distr_lab").range("F7").value
    else:
        ax=sns.distplot(data,bins=bins,ax=ax)
            #Ploting percentile lines
    if perc=="Yes":
        perc=eval(wb.sheets("distr_lab").range("F10").value)
        for value in perc:
            ax.plot([np.percentile(data,value) for i in range(10)],np.linspace(0,max(np.histogram(data,bins=bins,density=True)[0])*1.1,10))
            ax.text(np.percentile(data,value),max(np.histogram(data,bins=bins,density=True)[0])*1.1,s="P"+str(value),fontsize=7)
            #Settting titles
    ax.set_xlabel(variable_name)
    ax.set_title(wb.sheets("distr_lab").range("F3").value+s)
        #Now, lets see how its look
    direct=wb.sheets("distr_lab").range("G1")
    wb.sheets("distr_lab").pictures.add(mpl_fig,name="fig1",top=direct.top,left=direct.left)
    #Save fig
    if save_pict=="Yes":
        mpl_fig.savefig(os.path.join(path_p,wb.sheets("distr_lab").range("F2").value+s)+".jpeg",format="jpeg",dpi=500)
    return fit_distr

def plot_hist():
    '''''
    This function make a masive plot of experimental data in case user wanna make a distribution fit
    '''''
    aprox={}
    wb2=xw.Book.caller()
    path = wb2.sheets("xlwings.conf").range("B8").value
    path_p=os.path.join(path,"graph","histograms_"+wb2.sheets("distr_lab").range("F2").value)
    statusbar=wb2.macro("set_statusbar")
    #Preparing working data
    data=np.array(wb2.sheets("distr_lab").range("A3:A5000").value,dtype=str)
    data=np.delete(data,np.where(data=="None"))
    data=data.astype(float)
    mean_data=np.average(data)
    #Read distribution lists
    with open(sys.executable.replace("python.exe","distr.txt"),"r") as f:
        distr=eval(f.read())
    #Making plots
    if wb2.sheets("distr_lab").range("F5").value=="No":
        #If user don't wanna fit the distribution
        statusbar("ploting your data")
        plot_hist_ies(wb2)
        statusbar("done")
    else:
        #In case user wanna fit distribution
        for i in distr.keys():
            statusbar("ploting "+i+" distribution")
            try:
                wb2.sheets("distr_lab").range("F7").value=i
                a=plot_hist_ies(wb2)
                aprox[i]=a
            except:
                pass
        #making report
            #This process compare histograms to make better fir indicator
        if int(0.1*len(data))<5:
            bins=5
        elif int(0.1*len(data))>10:
            bins=10
        else:
            bins=int(0.1*len(data))
        data_freq=np.histogram(data,bins=bins)[0]/np.sum(np.histogram(data,bins=bins)[0])
        excel=xw.App(visible=False)
            #Prepare excel tables
        wb3=xw.Book()
        statusbar("creating table")
        wb3.sheets[0].name="report"
        wb3.sheets("report").range("A1").value="Distribution"
        wb3.sheets("report").range("B1").value="Parameters"
        wb3.sheets("report").range("C1").value="Mean"
        wb3.sheets("report").range("D1").value="Std"
        wb3.sheets("report").range("E1").value="Mean_error"
        wb3.sheets("report").range("F1").value="histogram_error"
        wb3.sheets("report").range("H1").value="Datas_mean"
        wb3.sheets("report").range("I1").value=np.average(data)
        wb3.sheets("report").range("H2").value="Datas_std"
        wb3.sheets("report").range("I2").value=np.std(data)
        i=-1
        #setting report
        for distri in aprox.keys():
            i=i+1
            statusbar("filling "+distri+" distribution data")
            try:
                wb3.sheets("report").cells(2 + i, 1).value = distri
                wb3.sheets("report").cells(2 + i, 2).value = str(
                    [distr[distri][j] + str(aprox[distri][j]) for j in range(len(distr[distri]))])
                wb3.sheets("report").cells(2 + i, 3).value = eval(
                    "sp." + distri + "(" + str(aprox[distri]) + ").mean()")
                wb3.sheets("report").cells(2 + i, 4).value = eval("sp." + distri + "(" + str(aprox[distri]) + ").std()")
                wb3.sheets("report").cells(2 + i, 5).value = abs(
                    wb3.sheets("report").cells(2 + i, 3).value - wb3.sheets("report").range("I1").value)
                error=0
                samples=lhs(3000)
                variant=eval("sp."+distri+str(aprox[distri])+".ppf(samples)")
                freq_variant=np.histogram(variant,bins=bins)[0]/np.sum(np.histogram(variant,bins=bins)[0])
                for freq in range(bins):
                    error=error+abs(freq_variant[freq]-data_freq[freq])
            except:
                wb3.sheets("report").cells(2 + i, 2).value ="N/A"
                wb3.sheets("report").cells(2 + i, 3).value = "N/A"
                wb3.sheets("report").cells(2 + i, 4).value = "N/A"
                wb3.sheets("report").cells(2 + i, 5).value = "N/A"
                error="N/A"
                pass
            wb3.sheets("report").cells(2+i,6).value=error
            error=0
        wb3.sheets.add("recommend")
        aux = np.array(wb3.sheets("report").range("F2:F200").value, dtype="str")
        aux1 = np.delete(aux, np.where(aux == "None"))
        aux2 = np.array(wb3.sheets("report").range("A2:A" + str(len(aux1) + 1)).value, dtype="str")
        aux3 = np.array(wb3.sheets("report").range("B2:B" + str(len(aux1) + 1)).value, dtype="str")
        aux = ""
        aux = pd.DataFrame.from_dict({"distr": aux2, "error": aux1, "param": aux3})
        aux = aux.sort_values("error")
        aux = aux[0:20]
        for i in range(20):
            distr_fited = aux["distr"].iloc[i]
            statusbar("recommending functions based on distribution fitted: distribution " + distr_fited)
            rng = wb3.sheets("recommend").cells(1 + 11 * i, 1)
            wb3.sheets("recommend").pictures.add(os.path.join(path_p,wb2.sheets("distr_lab").range("F2").value+
                                                              "_distr_"+distr_fited + ".jpeg"), top=rng.top, left=rng.left)
            wb3.sheets("recommend").pictures[i].height = 150
            wb3.sheets("recommend").pictures[i].width = 250
            wb3.sheets("recommend").cells(4 + 11 * i, 6).value = "distr name"
            wb3.sheets("recommend").cells(4 + 11 * i, 7).value = aux["distr"].iloc[i]
            wb3.sheets("recommend").cells(5 + 11 * i, 6).value = "parameters"
            wb3.sheets("recommend").cells(5 + 11 * i, 7).value = aux["param"].iloc[i]
            wb3.sheets("recommend").cells(6 + 11 * i, 6).value = "error"
            wb3.sheets("recommend").cells(6 + 11 * i, 7).value = aux["error"].iloc[i]
        wb3.save(os.path.join(path_p,"report.xlsx"))
        wb3.close()
        #excel.kill()
        statusbar("done")

def plot_database():
    wb=xw.Book.caller()
    path=wb.sheets("xlwings.conf").range("B8").value
    if not os.path.exists(os.path.join(path,"Graph",wb.sheets("distr_lab").range("BCH1").value,"economics")):
        os.makedirs(os.path.join(path,"Graph",wb.sheets("distr_lab").range("BCH1").value,"economics"))
    if not os.path.exists(os.path.join(path,"Graph",wb.sheets("distr_lab").range("BCH1").value,"vector")):
        os.makedirs(os.path.join(path,"Graph",wb.sheets("distr_lab").range("BCH1").value,"vector"))
    yeari=wb.sheets("distr_lab").range("BCH4").value
    folder=wb.sheets("distr_lab").range("BCH1").value
    perc=np.array(eval(wb.sheets("distr_lab").range("BCH3").value))
    #Here we plot time series
    for file in os.listdir(os.path.join(path,"Runs",folder)):
        if file[0]=="V":
            fig, ax=plt.subplots()
            p={}
            for perce in perc:
                p["p"+str(int(perce))]=np.empty(0)
            aux=pd.read_csv(os.path.join(os.path.join(path,"Runs",folder),file),header=0,index_col=0)
            for i in range(len(aux.iloc[0])):
                for j in range(len(perc)):
                    p["p"+str(int(perc[j]))]=np.append(p["p"+str(int(perc[j]))],np.percentile(aux[str(i)],int(perc[j])))
            year=np.array([int(yeari+j) for j in range(len(aux.iloc[0]))])
            if wb.sheets("distr_lab").range("BCH2").value=="Percentile" or wb.sheets("distr_lab").range("BCH2").value=="All_dat+Perc":
                t=0
                for perce in perc:
                    t=t+5
                    ax.plot(year,p["p"+str(int(perce))],linewidth=4,zorder=5*t,alpha=0.75)
                ax.legend([int(i) for i in perc])
            if wb.sheets("distr_lab").range("BCH2").value=="All_data" or wb.sheets("distr_lab").range("BCH2").value=="All_dat+Perc":
                for i in range(len(aux[str(0)])):
                    ax.plot(year,aux.iloc[i],linestyle=":")
            ax.set_title(file.replace(".csv","").replace("Vector_",""))
            ax.set_xlabel("year")
            ax.set_ylabel("caudal")
            ax.grid()
            fig.savefig(os.path.join(path,"Graph",folder,"vector",file.replace(".csv",".jpeg")),format="png",dpi=500)
            plt.close()
    #And here we plot another non-vectorial answers
    aux=pd.read_csv(os.path.join(path,"Runs",folder,"economics.csv"),header=0,index_col=0)
    for label in aux.axes[1]:
        if label[0]!="D" and label[len(label)-3]!="P":
            fig, ax=plt.subplots()
            maxy=max(np.histogram(aux[label],density=False)[0])
            maxx=max(np.histogram(aux[label],density=False)[1])
            minx=min(np.histogram(aux[label],density=False)[1])
            ax.hist(aux[label])
            for perce in perc:
                value=np.percentile(aux[label],perce)
                ax.plot([value for i in range(10)],np.linspace(0,maxy,10))
                ax.text(value+abs(maxx-minx)*0.009,maxy-2,s=str(round(np.percentile(aux[label],perce),2)),fontsize=6)
            ax.set_title("histogram_"+label)
            ax.set_xlabel(label)
            ax.legend(["P"+str(int(perce)) for perce in perc])
            fig.savefig(os.path.join(path,"Graph",folder,"economics",label+".jpeg"),format="png",dpi=500)
            plt.close()
    with open(os.path.join(path,r"Runs",folder, r"readme.txt"), "r") as f:
        text=f.read()
    f.close()
    with open(os.path.join(path,r"graph",folder, r"readme.txt"), "w") as f:
        f.write(text)
    f.close()

def go_databaseplot():
    wb=xw.Book.caller()
    wb.sheets("distr_lab").range("BCM2:BCM5000").clear_contents()
    path = wb.sheets("xlwings.conf").range("B8").value
    wb.sheets("distr_lab").range("BCM2").options(transpose=True).value=os.listdir(os.path.join(path,"Runs"))
    wb.sheets("distr_lab").range("BCL1").select()
