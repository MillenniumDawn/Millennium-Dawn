population = 1000000000
population_k = 0
population_temp = 0
years = 0
population_yearly_growth_base = 0.01
sum_of_modifiers = 0.50

if population > 0:
    print('Starting population is:', population)
population_k = population / 1000 #Should convert manpwoer to k
print('\nPopulation in thousands:',population_k,'\n')

while years <= 30:
    population_k = round(population_k * (1 + ((population_yearly_growth_base/12) * (1 + sum_of_modifiers))), 3)
    if population_k > 2147483.647 :
        print ('Test failed at year ', years)
    else:
        print ('Test passed. Value is:', population_k, 'at year', years)
    years = years + 1

##NCountry.POPULATION_YEARLY_GROWTH_BASE/12 * (1+<global_monthly_population modifier of controller country>) * <state's current total population>
