# -*- coding: utf-8 -*-
"""
Created on Mon Aug 07 13:48:04 2017

@author: Xian_Work

This file creates diagnostic plots of the series generated by a set of parameters,
 compared against a model target. The sim_plot class has methods for adding a
 consumption and search model targets of arbitrary length, for adding a weighting
 matrix from a variance/covariance matrix, for computing and adding a series
 from a given set of parameters, and for making comaprions plots.
 
 The add_agent method supports both representative agents and mixes of heterogeneous
 agents. For representative agents, a name, an employment history, the point in 
 the employment history to begin computing the consumption history, the point to
 begin computing the search history, and the parameter dictionary must be specified.
 For heteoregenous agent, a list of (weight,dictionary) tuples must be specified
 iunstead, with weights summing to 1.
"""

import plotnine as p9
param_path="../Parameters/params_ui.json" 
execfile("prelim.py")

###Plot aesthetics###
aes_color = p9.scale_color_brewer(type = 'qual', palette = 2)
aes_color_alpha = 0.7
aes_glyphs = p9.scale_shape_manual(values = ['o', '^', 's', 'D', 'v', 'x', 'P', '+'])
aes_fte_theme = p9.theme(axis_ticks = p9.element_blank(),
                         panel_background = p9.element_rect(fill='white', color='white'),
                         panel_border = p9.element_rect(color='white'),
                         panel_grid_minor = p9.element_blank(),
                         panel_grid_major = p9.element_blank(),
                         legend_background = p9.element_rect(fill='white'),
                         legend_text = p9.element_text(size = 8),
                         legend_key = p9.element_blank(),
                         legend_title = p9.element_blank(),
                         plot_title = p9.element_text(size =12, vjust = 1.25, ha='center'),
                         axis_text_x = p9.element_text(size =10),
                         axis_text_y = p9.element_text(size =10),
                         axis_title_x = p9.element_text(size =10, margin = {'t':10.0}),
                         axis_title_y = p9.element_text(size =10, angle = 90),
                         )
aes_model_xlab = p9.labels.xlab("Months Since First UI Check")
aes_onset_line = p9.geom_vline(xintercept = -1.5, linetype = '--', color = '#999999')
aes_exhaust_line = p9.geom_vline(xintercept = 5.5, linetype = '--', color = '#999999')
aes_exhaust_line_FL = p9.geom_vline(xintercept = 3.5, linetype = '--', color = '#999999')

                                    
########################################################
# Functions for generating consumption and search series 
########################################################
def norm(m_model, index):
        """Normalizes a series relative to the value at index"""
        out=copy.deepcopy(m_model)
        denom=copy.deepcopy(m_model[index])
        for i in range (len(m_model)):
            out[i]=m_model[i]/denom
        return(out)
    
def compute_dist(m_model, m_hat, w_mat):
        """Computes the weighted distance between a model and the data moments"""
        diff=np.asmatrix(m_model-m_hat)
        dist=diff*w_mat*diff.T
        return(dist[0,0])


def gen_model_target(data_cons, data_search, c_start, c_len, s_start, s_len, onset):
    """Generates the combined consumption and search series to use as a model target
    
    Args:
        data_cons:      The consumption series to subset model target from
        data_search:    The search series to subset model target from
        c_start:        Index to start subsetting consumption
        c_len:          Length of consumption series to subset
        s_start:        Index to start subsetting search
        s_len:          Length of search series to subset
        onset:          Index of UE onset, i.e. index of t=-1
        
    Returns:
        Model target of length c_len + s_len, with consumption first
     
    """
    c_target=data_cons[c_start:c_len+c_start]
    s_target=data_search[s_start:s_len+s_start]
    m_hat=np.append(c_target,s_target)
    return m_hat, c_len, s_len, onset
    


#Function to handle evolving shares
def gen_evolve_share_series(emp_hist,cons_start,search_start,
                            periods,norm_time,*args, **kwargs):
    """Generates consumption and hazard series with evolving shares
    
    The generated consumption and search series will be of equal length, with
    dummy zeros filled in for search prior to the specified date.
    
    This is used in grid_sims_ss and in model_plotting.
    
    Args:
        emp_hist:       Base employment hist
        con_start:      Point in emp_hist to start generating cons and search series
        search_start:   Before this index in search series, search is 0 (dummy)
        periods:        Length of series to generate
        norm_time:      Point in series to normalize consumption (usually just prior to onset)
        *args:          List of (weight,p_d) tuples
        verbose:        Whether to generate the df and the component series
        normalize:      Whether to normalize the data
        w_check:        Whether to check if weights sum to 1
        
    Returns:
        out_dict, with the following keys:
            'df':           Working dataframe
            'cons_ind':     Dict of individual cons series
            'search_ind':   Dict of individual hazard series
            'w_cons_out':   Weighted cons series, normalized
            'w_search_out': Weighted search series
            
    The agent.compute_series() method computes the consumption and search 
    series for every period of the employment history. However, it only saves
    and uses for comparison a sub-series of length equal to the 'periods' 
    argument, starting from the cons_start argument.
    """
    num_agents=len(args)
    verbose=kwargs.get("verbose",False)
    normalize=kwargs.get("normalize",True)
    w_check=kwargs.get("w_check",True)
    
    
    #Check weights and store
    if w_check:
        sumweights=0.0
        for arg in args:
            sumweights += arg[0]
        if not np.isclose(1,sumweights):
            raise ValueError("Weights must sum to 1!")
            
    shares_df=pd.DataFrame()
    shares_df['type']=range(num_agents)
    w_init=[]
    for arg in args:
        w_init.append(arg[0])
    shares_df['w_init']=w_init
        
    #Generate consumption and search series for each type
    cons_comb=[]
    search_comb=[]
    for arg in args:
        weight=arg[0]
        p_d=arg[1]
        agent=solve_search.agent_series(p_d)
        agent.solve_agent()
        if not np.isclose(p_d['beta_hyp'], 1):
            agent.solve_agent_hb()
        agent.compute_series(e=emp_hist,T_series=len(emp_hist)-1)
        
        cons=agent.c_save[cons_start:cons_start+periods]
        #search is over the same span as consumption, with dummy zeros
        #hazard in last period is same as prev period
        search=agent.s_save[cons_start:cons_start+periods]
        for i in range(search_start-cons_start):
            search[i]=0
        #add to combined list
        cons_comb+=list(cons)
        search_comb+=list(search)
        
    #Generate corresponding series of types
    type_comb=[]
    for i in range(num_agents):
        type_comb+= [i]*periods
        
    #Group data in dataframe
    df=pd.DataFrame()
    df['cons']=cons_comb
    df['haz']=search_comb
    df['type']=type_comb
    df['e_hist_index']= range(0,periods)*num_agents
    
    #Lagged hazard rate and remainders
    df['haz_tm1']=df.groupby('type', as_index=False)['haz'].shift()
    df['haz_tm1'].fillna(0, inplace=True)
    df['1_minus_haz'] = 1 - df['haz']
    df['1_minus_haz_tm1'] = 1 - df['haz_tm1']
    
    #Merge in initial weight, create type pop. per period    
    df = pd.merge(df, shares_df, on='type')
    df['remaining frac of tot. init. pop.'] = df['w_init'] * df.groupby('type')['1_minus_haz_tm1'].cumprod()

    #create total pop per period, and shares per period
    period_total_pop=df.groupby('e_hist_index', as_index=False)['remaining frac of tot. init. pop.'].sum()
    period_total_pop.rename(
        columns={'remaining frac of tot. init. pop.': 'total pop'},
        inplace=True
    )
    
    df = pd.merge(df, period_total_pop, on='e_hist_index')
    df['current_period_share']=df['remaining frac of tot. init. pop.'] / df['total pop']
    df = df.sort_values(by=['type', 'e_hist_index'])
            
    #Create lagged consumption change
    df['delta_c']=df.groupby('type')['cons'].pct_change()
    df['w_delta_c']=df['delta_c']*df['current_period_share']
       

    #weighted consumption changes
    tot_delta_c=df.groupby('e_hist_index', as_index=False)['w_delta_c'].sum()
    tot_delta_c=tot_delta_c['w_delta_c']
    
    #Combined output series
    w_cons_out=np.zeros(periods)
    
    if normalize:   #If normalizing consumption:
        w_cons_out[norm_time]=1
    else:           #If not use the naive consumption
        df['w_cons_naive']=df['current_period_share']*df['cons']
        cons_series_naive=df.groupby('e_hist_index',as_index=False)['w_cons_naive'].sum()
        w_cons_out[norm_time]=cons_series_naive['w_cons_naive'][norm_time]
    
    #periods before normalization point, using changes
    for i in range(norm_time-1,-1,-1):
        w_cons_out[i]=w_cons_out[i+1]/(1+tot_delta_c[i+1])
    #periods after normalization point, using changes
    for i in range(norm_time+1,len(w_cons_out)):
        w_cons_out[i]=w_cons_out[i-1]*(1+tot_delta_c[i])
        
    #Weighted search hazards
    df['w_haz']=df['haz']*df['current_period_share']
    w_search_out=df.groupby('e_hist_index')['w_haz'].sum()
    
    out_dict={'w_cons_out':w_cons_out,
              'w_search_out':w_search_out                
            }
    if verbose:
         #consumption and search for individual agent type
        cons_ind={}
        search_ind={}
        share_ind={}
        cons_bytype=df.groupby('type')['cons']
        search_bytype=df.groupby('type')['haz']
        share_bytype=df.groupby('type')['current_period_share']
        for agent_type, cons in cons_bytype:
            cons_ind.update({agent_type:cons})
        for agent_type, search in search_bytype:
            search_ind.update({agent_type:search})
        for agent_type, share in share_bytype:
            share_ind.update({agent_type:share})
        
        out_dict.update({'df':df,
                         'cons_ind':cons_ind,
                         'search_ind':search_ind,
                         'share_ind':share_ind
                         })
    return out_dict 


#################
#Simulation agent
#################
class sim_plot():
    def __init__(self):
        self.agents=[]
        self.cons_target=None
        self.search_target=None
        
    def add_mhat(self, data_spend, data_search):
        """Add the consumption and search data as a vector
    
        data_spend and data_search should be equal length vectors
        """ 
        #Save data
        if len(data_spend) != len(data_search):
            raise Exception('Data not of same length! Pad search with dummy values')
        else:
            self.data_spend=data_spend
            self.data_search=data_search
    
    def add_cons_target(self,start,end,vcv):
        """Create a consumption only target by subsetting mhat"""
        self.cons_target=self.data_spend[start:end]
        self.cons_wmat=np.linalg.inv(vcv)
        self.periods=len(self.cons_target)
        
    def add_search_target(self,start,end,vcv):
        """Create a search only target by subsetting mhat"""
        self.search_target=self.data_search[start:end]
        self.search_wmat=np.linalg.inv(vcv)
        
    def add_data_CI(self, cons_se, search_se):
        """Adds CIs of 1.96*SD around cons_target and search_target. Must
        be specified in plotting function to actually show CIs"""
        #Consumption lower and upper bounds
        self.cons_lower = []
        self.cons_upper = []
        for i in range(len(self.cons_target)):
            self.cons_lower.append(self.cons_target[i] - 1.96*cons_se[i])
            self.cons_upper.append(self.cons_target[i] + 1.96*cons_se[i])
            
        #Search lower and upper bounds            
        self.search_lower = []
        self.search_upper = []
        for i in range(len(self.search_target)):
            self.search_lower.append(self.search_target[i] - 1.96*search_se[i])
            self.search_upper.append(self.search_target[i] + 1.96*search_se[i])

        
    def pop_series(self):
        """
        Pops the most recently added series
        """
        return self.agents.pop()
    
    def add_series(self, name, cons_series, search_series):
        '''
        Directly adds two arrays as a consumption and search series
        
        Args:
            name: Name of Series
            cons_series: consumption series
            search_series: search series
        '''

        agent_dict={
                'cons'      :cons_series,
                'search'    :search_series,
                'name'      :name
                }
        if self.cons_target:
            cons_dist=compute_dist(cons_series,self.cons_target,self.cons_wmat)
            agent_dict.update({"cons_dist":cons_dist})
        if self.search_target:
            search_dist=compute_dist(search_series,self.search_target,self.search_wmat)
            agent_dict.update({"search_dist":search_dist})
        self.agents.append(agent_dict)       
        
        
    def add_agent(self, name, emp_hist, cons_start, search_start, norm_time, *args, **kwargs):
        """Compute and store the consumption and search series for an agent.
        
        Args:
            emp_hist:       Employment_history
            con_start:      point in emp_hist to start generating cons and search series
            search_start:   before this index in search series, search is 0 (dummy)
            norm_time:      point in series to normalize consumption (usually just prior to onset)
            *args:          List of (weight,p_d) tuples
            verbose:        whether to generate the df and the component series
            normalize:      whether to normalize the data
        
        Computes the consumption and search series for either a representative agent
        or the weighted average of a number of agents.
        """
        verbose=kwargs.get('verbose',False)
        normalize=kwargs.get('verbose',True)
     
        series_dict=gen_evolve_share_series(emp_hist,cons_start,search_start,
                                            self.periods,norm_time,*args,
                                            verbose=verbose, normalize=normalize)
        cons=series_dict['w_cons_out']
        search=series_dict['w_search_out'][search_start-cons_start:search_start-cons_start+len(self.search_target)]
             
          
        #Store results
        agent_dict={
                'cons'      :cons,
                'search'    :search,
                'name'      :name
                }
        if self.cons_target:
            cons_dist=compute_dist(cons,self.cons_target,self.cons_wmat)
            agent_dict.update({"cons_dist":cons_dist})
        if self.search_target:
            search_dist=compute_dist(search,self.search_target,self.search_wmat)
            agent_dict.update({"search_dist":search_dist})
        if verbose:
            agent_dict.update({'df':series_dict['df'],
                               'cons_ind':series_dict['cons_ind'],
                               'search_ind':series_dict['search_ind'],
                               'share_ind':series_dict['share_ind']
                               })
        self.agents.append(agent_dict)       
    
        
                
    def plot(self, cons_filename, cons_title, search_filename, search_title, 
             cons_legend_loc=(0.30,0.22), search_legend_loc=(0.30,0.22),
             cons_t0=-5, show_data_CI = False,
             cons_ylim=(0.7,1.03), search_ylim=(0,0.35), search_xlim=(0,10),
             extend_left=False,tminus5=True,
             GOF=False,GOF_combine=False,
             show_data=True, show_models=True,
             florida=False,
             cons_ylab="Ratio to t= -2",
             search_ylab="Job-Finding Hazard"):
        """Make a plot of all the stored series
    
        Initialize the base plot from the m_hat data, then use the ggsave function from make_plots.py
        to plot the base plot as well as all of the consumption series generated by stored agents.
        
        Do the same for all of the search series on a separate plot.
        Args:
            cons_filename:      Filename for consumption plot
            cons_title:         Title for consumption plot     
            search_filename:    Filename for search plot
            search_title:       Title for search plot     
            loc_cons:           Position for legend in consumption plot
            loc_search:         Position for legend in search plot
            cons_t0:            Time when consumption series starts,
                                relative to first UI check 
            show_data_CI:       Show confidence intervals around data
            cons_ylim:          y-limits for consumption plot                                
            search_ylim:        y-limits for search plot
            cons_xlim:          x-limits for consumption plot                                
            extend_left:        Whether to extend x-lims to start from t=-12
            tminu5:             Set breaks correctly when plot is from t=-5
            GOF:                Display GOF measures or not
            GOF_combine:        Whether to show GOF separately or in total for each plot
            show_data:          Whether to plot the data
            show_models:        Whether to plot the models
            florida:            Where to show the exhaustion line
            cons_ylab:          Consumption plot y-axis label
            search_ylab:        Search plot y-axis label
        
        """
        self.cons_plot = pd.DataFrame()
        self.search_plot = pd.DataFrame()
                
        mos_since_start_cons = range(cons_t0, len(self.cons_target)+cons_t0)
        mos_since_start_search = range(0, len(self.search_target))
        
        if show_data:
            cons_base = {"value":self.cons_target,'mos_since_start':mos_since_start_cons,
                         "lower":self.cons_lower, "upper":self.cons_upper,
                         'variable':['Data'] * len(mos_since_start_cons)}
            self.cons_plot = self.cons_plot.append(pd.DataFrame(cons_base))
            
            
            search_base = {"value":self.search_target,'mos_since_start':mos_since_start_search,
                         "lower":self.search_lower, "upper":self.search_upper,
                         'variable':['Data'] * len(mos_since_start_search)}
            self.search_plot = self.search_plot.append(pd.DataFrame(search_base))
            
        if show_models:
            for agent in self.agents:
                #Save each consumption and search series as a key-value pair
                cons_label = copy.deepcopy(agent['name'])
                search_label = copy.deepcopy(agent['name'])
                if GOF==True:
                    GOF_cons = int(agent['cons_dist'])
                    GOF_search = int(agent['search_dist'])
                    if GOF_combine==False:
                        cons_GOF_label=", GOF=" + str(GOF_cons)
                        search_GOF_label=", GOF=" + str(GOF_search)
                        cons_label +=cons_GOF_label
                        search_label+=search_GOF_label
                        print(cons_label)
                        print(search_label)
                       
                    else:
                        GOF_label=", GOF=" + str(GOF_cons + GOF_search)
                        cons_label+=GOF_label
                        search_label+=GOF_label
                    if florida==True:
                            search_label = copy.deepcopy(agent['name'])
                        
                cons_series={'value':list(agent['cons']),
                             'mos_since_start':mos_since_start_cons,
                             'lower':list(agent['cons']), #dummy CI of width 0
                             'upper':list(agent['cons']),  #dummy CI of width 0
                             'variable':[cons_label]*len(mos_since_start_cons)}
                search_series={'value':list(agent['search']),
                             'mos_since_start':mos_since_start_search,
                             'lower':list(agent['search']), #dummy CI of width 0
                             'upper':list(agent['search']),  #dummy CI of width 0
                             'variable':[search_label]*len(mos_since_start_search)}
       
                #Append to the list of agents to plot
                self.cons_plot = self.cons_plot.append(pd.DataFrame(cons_series))
                self.search_plot = self.search_plot.append(pd.DataFrame(search_series))
                    
                def plot_base_temp(df):
                    pp = p9.ggplot(df, p9.aes(x='mos_since_start', y='value',
                                              group='variable',colour='variable',
                                              shape = 'variable', linetype = 'variable'))
                    pp = pp + p9.geom_line(alpha = aes_color_alpha) +\
                         p9.geom_point(show_legend=True, alpha = aes_color_alpha) +\
                         aes_color + aes_glyphs +\
                         p9.theme_bw(base_size=9) + aes_fte_theme + aes_model_xlab                                  
                    return pp
                
                def plot_add_CIs(pp):
                    return pp + p9.geom_linerange(mapping = p9.aes(x='mos_since_start',
                                                                     ymin = 'lower',
                                                                     ymax ='upper'),
                                                    show_legend=False,
                                                    alpha = aes_color_alpha)
                def add_FL_exhaust_line(pp, FL=False):
                    '''If FL=True, adds a line at x=3.5, else adds at x=5.5'''
                    if FL==True:
                        pp=pp + aes_exhaust_line_FL
                    else:
                        pp=pp + aes_exhaust_line
                    return pp
                
                #Consumption plot
                cons_plot_out = plot_base_temp(self.cons_plot)  
                cons_plot_out += p9.labels.ylab(cons_ylab)
                cons_plot_out += p9.labels.ggtitle(cons_title)
                cons_plot_out += p9.scales.ylim(cons_ylim)
                cons_plot_out += p9.scale_x_continuous(breaks =[-5, 0, 5, 10])
                cons_plot_out += p9.theme(legend_position = cons_legend_loc)
                
                #Job search plot
                search_plot_out = plot_base_temp(self.search_plot)  
                search_plot_out += p9.labels.ylab(search_ylab)
                search_plot_out += p9.labels.ggtitle(search_title)
                search_plot_out += p9.scales.ylim(search_ylim)
                search_plot_out += p9.scale_x_continuous(breaks =[-5, 0, 5, 10])
                search_plot_out += p9.theme(legend_position = search_legend_loc)
                
                #Add exhaustion line
                cons_plot_out = add_FL_exhaust_line(cons_plot_out, FL=florida)
                search_plot_out = add_FL_exhaust_line(search_plot_out, FL=florida)
                
                #Add confidence intervals on data
                if show_data:
                    if show_data_CI == True:
                        cons_plot_out = plot_add_CIs(cons_plot_out)
                        search_plot_out = plot_add_CIs(search_plot_out)
                
                #Save plots
                if not(cons_filename is None):     
                    cons_plot_out.save('../out/' + cons_filename + '.pdf', width =7, height = 4, verbose=False)        
                if not(search_filename is None):     
                    search_plot_out.save('../out/' + search_filename + '.pdf', width =7, height = 4, verbose=False)

            
#################################################
#Helper Functions - Plots 
################################################

#Function to add heterogenous agent
def mk_mix_agent(params_dict, params,vals,weights):
    """Return a list of (weight, param_dict) value pairs that can be added to a plot_sim object as a mixed agent
    
    p_d is the initial parameter dictionary. params is a vector of the params in params_dict to vary.
    vals is a vector of the values each agent takes for the values in params. weights is a vector
    of weights. name specifies the name of the agent.
    
    When submitting to add_agent, unpack the mix_agent argument with '*' as follows:
    plots.add_agent(name, *agentname)
    """
    agent_list=[]
    for i in range(len(weights)):
        p_d=copy.deepcopy(params_dict)
        for j in range(len(params)):
            param=params[j]
            p_d[param]=vals[i][j]
        agent=(weights[i],p_d)
        agent_list.append(agent)
        
    return agent_list

def opt_dict_csv_in(filename, param_list=["k","phi","beta_var","rho","beta_hyp","L_","opt_type","dist"]):
    """Returns a list of dictionaries of optimized parameters
    
    Args:
      filename : the filepath of the csv file to read
      param_list: the list of parameters to read in
    
    """
    
    infile=filename    
    dicts=[]
    param_list=param_list
    print(param_list)
    
    with open(infile, "rb") as file:
        reader=csv.DictReader(file)
        for row in reader:
            if row['dist']=='dist':
                print('Not a result row!')
            else:
                out_dict={}            
                for key in param_list:
                    try:
                        out_dict.update({key:row[key]})
                    except:
                        print("key not found!")
                for key in out_dict.keys():
                    if key!='opt_type' and key!='dist':
                        out_dict[key]=float(out_dict[key])
                dicts.append(out_dict)
            
    return dicts


def make_base_plot(c_start,c_len,s_start,s_len,
                   data_cons,data_search,cons_se,search_se):
    """
    Creates a plot with a consumption and search target
    
    Args:
        c_start:    Index to start generating consumption target from data
        c_len:      Length of consumption target
        s_start:    Index to start generating search target from data
        s_len:      Length of search target   
        data_cons:  Raw consumption data
        data_search:Raw search data
        cons_se:    Standard errors of consumption series (length=c_len)
        search_se:  Standard errors of search series (length=s_len)
    """
    c_end=int(c_start+c_len)
    s_end=int(s_start+s_len)
    
    cons_var=np.square(cons_se)
    cons_vcv=np.diag(cons_var)
    cons_vcv=np.asmatrix(cons_vcv)
    
    search_var=np.square(search_se)
    search_vcv=np.diag(search_var)
    search_vcv=np.asmatrix(search_vcv)
        
    base_plot=sim_plot()
    base_plot.add_mhat(data_cons,data_search)
    base_plot.add_cons_target(c_start,c_end,cons_vcv)
    base_plot.add_search_target(s_start,s_end,search_vcv)
    
    base_plot.add_data_CI(cons_se = cons_se, search_se = search_se)
    return base_plot

