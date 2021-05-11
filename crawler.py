# ----------------------------------------------------------------------
# Purpose: Crawl the web for information on Covid-19 for User-specified
#          countries
#
# Author(s): Katy Cooperstein, Manjari Maheshwari
# ----------------------------------------------------------------------
"""

"""
import urllib.parse
import urllib.error
import urllib.request
import bs4
import pandas as pd


def country_info(seed, pop_url, search_term):
    """
    Crawl the web to extract necessary information on covid-19 based on
    countries that contain the user's search_term
    :param seed: (string) address of webpage containing pandemic
                          information
    :param pop_url: (string) address of webpage containing
                             population information
    :param search_term: (string) search term required in country's name
                                 inputted from user
    """
    data_soup = visit_url(seed)
    covid_data = crawl(data_soup)
    for each_country in covid_data.index:
        if search_term in each_country:
            cases, deaths = covid_data.loc[each_country, [0, 1]]
            url = urllib.parse.urljoin(seed, covid_data.loc[each_country, 2])
            p = paragraph(url, each_country)
            pop_soup = visit_url(pop_url)
            pop_series = access_pop(pop_soup)
            population = pop_series.loc[each_country]
            format_file(search_term, each_country, population, cases,
                        deaths, p)


def format_file(search_term, name, population, cases, deaths, p):
    """
    Publish all relevant information into a formatted text file
    :param search_term: (string) search term required in country's name
    :param name: (string) name of the country containing search_term
    :param population: (string) population of the country
    :param cases: (string) representation of current number of covid-19
                           cases in given country
    :param deaths: (string) representation of current number of deaths
                            from covid-19 in given country
    :param p: (string) first non-empty visible paragraph from country's
                       individual pandemic page
    """
    filename = f'{search_term.lower()}summary.txt'
    f = open(filename, 'a+')
    f.write("\nCountry: %s\n" % name)
    f.write("Population: %29s\n" % population)
    f.write('Total Confirmed Cases: %18s\n' % cases)
    f.write('Total Deaths: %27s\n' % deaths)
    cases_per, deaths_per = calculate(population, cases, deaths)
    f.write('Cases per 100,000 people: %17.1f\n' % cases_per)
    f.write('Deaths per 100,000 people: %16.1f\n' % deaths_per)
    f.write('%s\n' % p)
    f.close()


def calculate(population, cases, deaths):
    """
    Calculate the number of cases and deaths per 100,000 people in the
    specified country
    :param population: (string) population of the country
    :param cases: (string) representation of current number of covid-19
                           cases in given country
    :param deaths: (string) representation of current number of deaths
                            from covid-19 in given country
    :return: (tuple) (cases_per, deaths_per)
             cases_per: float of covid-19 cases per 100,000 people
             deaths_per: float of covid-19 deaths per 100,000 people
    """
    pop = float(population.replace(',', '')) / 100000
    num_cases = float(cases.replace(',', ''))
    num_deaths = float(deaths.replace(',', ''))
    cases_per = num_cases / pop
    deaths_per = num_deaths / pop
    return cases_per, deaths_per


def clean_country_names(cells, index):
    """
    Sanitize country names extracted from web crawler by removing extra
    appended symbols due to attached links
    :param cells: (ResultSet) set of columns of a beautiful soup
                              object's representation of HTML table
    :param index: (int) index of column that contains country names
    :return: (string) sanitized name of the country
    """
    country = cells[index].get_text().strip()
    if '[' in country:
        country = country.split('[')
        return country[0]
    else:
        return country


def access_pop(soup):
    """
    Parse the table retrieved from BeautifulSoup object to return a
    Panda Series of countries and their populations
    :param soup: (BeautifulSoup) object representing HTML input from
                                 population url
    :return: (Series) containing a string representation of population
                      information indexed by country name
    """
    table = soup.find('table', attrs={'class': "wikitable sortable"})
    rows = table.find_all('tr')
    countries = []
    populations = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) > 2:
            country = clean_country_names(cells, 1)
            countries.append(country)
            population = cells[2]
            populations.append(population.get_text().strip())
    pop_series = pd.Series(populations, index=countries)
    return pop_series


def crawl(soup):
    """
    Parse the table retrieved from BeautifulSoup object to return a
    Panda DataFrame of countries, covid-19 cases, deaths, and links for
    each country's individual pandemic page
    :param soup: (BeautifulSoup) object representing HTML input from
                                 seed url
    :return: (DataFrame) containing a string representation of cases,
                         deaths, and links indexed by country name
    """
    table = soup.find('table',
                      attrs={'class': "wikitable plainrowheaders sortable"})

    rows = table.find_all('tr')
    countries = []
    cases = []
    deaths = []
    links = []
    for row in rows:
        vals = row.find_all('th')
        cells = row.find_all('td')
        if len(cells) > 3:
            country = clean_country_names(vals, 1)
            countries.append(country)
            case = cells[0]
            cases.append(case.get_text().strip())
            death = cells[1]
            deaths.append(death.get_text().strip())
            for a in row.find_all('a'):
                all_links = [a.get('href', None)]
                for each_link in all_links:
                    if '/wiki' in each_link:
                        links.append(each_link)

    case_series = pd.Series(cases, index=countries)
    death_series = pd.Series(deaths, index=countries)
    link_series = pd.Series(links, index=countries)
    covid_data = pd.concat([case_series, death_series, link_series], axis=1)
    return covid_data


def paragraph(url, search_term):
    """
    Crawl the url of the specified country's individual pandemic page
    to return the first non-empty visible paragraph
    :param url: (string) the address of the web page to be read
    :param search_term: (string) search term required in country's name
    :return: (string) the first non-empty visible paragraph from the
                      country's individual pandemic page
    """
    soup = visit_url(url)
    para_list = []
    for para in soup.find_all('p'):
        if search_term in para.get_text():
            para_list.append(para.get_text())
    return para_list[0]


def visit_url(url):
    """
    Open the given url and return a BeautifulSoup object representing
    the webpage's HTML input
    :param url: (string) the address of the web page to be read
    :return: (BeautifulSoup) object that represents the input HTML doc
    """
    try:
        with urllib.request.urlopen(url) as url_file:
            bytes = url_file.read()
    except urllib.error.URLError as url_err:
        print(f'Error opening url: {url}\n{url_err}')
    else:
        soup = bs4.BeautifulSoup(bytes, 'html.parser')
        return soup


def main():
    seed = 'https://en.wikipedia.org/wiki/2019%E2%80%9320_coronavirus_' \
           'pandemic_by_country_and_territory'
    pop_url = 'https://en.wikipedia.org/wiki/List_of_countries_and_' \
              'dependencies_by_population'
    search_term = input("Enter a country to search: ").title()
    country_info(seed, pop_url, search_term)


if __name__ == "__main__":
    main()
