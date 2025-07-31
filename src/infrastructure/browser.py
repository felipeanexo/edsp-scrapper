"""
Browser infrastructure for web scraping with improved navigation.
"""

import asyncio
from typing import List
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Page, BrowserContext
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.domain.entities import ScrapingConfig
from src.infrastructure.logger import structured_logger


class BrowserManager:
    """Browser management with improved navigation capabilities."""

    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_concurrent)

    async def get_browser_context(self):
        """Get browser context for initial operations."""
        p = await async_playwright().start()
        browser = await p.chromium.launch(headless=self.config.headless)
        try:
            yield browser
        finally:
            await browser.close()
            await p.stop()

    async def create_browser_contexts(self, count: int = 3):
        """Create multiple browser contexts for parallel processing."""
        p = await async_playwright().start()
        browser = await p.chromium.launch(headless=self.config.headless)
        contexts = []

        for i in range(count):
            context = await browser.new_context()
            contexts.append(context)

        try:
            yield browser, contexts
        finally:
            for context in contexts:
                await context.close()
            await browser.close()
            await p.stop()

    async def get_total_institutions(self, page: Page) -> int:
        """Get total number of institutions from dataTables_info div."""
        try:
            # Wait for the dataTables_info div to be available
            await page.wait_for_selector("#tabelabusca_info", timeout=10000)

            # Get the text content
            info_div = await page.query_selector("#tabelabusca_info")
            if info_div:
                text = await info_div.text_content()
                if text:
                    # Extract the total number from "Mostrando de 1 até 100 de 5.574 registros"
                    import re

                    match = re.search(r"de (\d+(?:\.\d+)?) registros", text)
                    if match:
                        total_str = match.group(1).replace(
                            ".", ""
                        )  # Remove dots from thousands
                        total_institutions = int(total_str)

                        structured_logger.bind_context(
                            action="total_institutions_detected",
                            total_institutions=total_institutions,
                        ).info(f"🏫 Total institutions detected: {total_institutions}")

                        return total_institutions

            structured_logger.bind_context(
                action="total_institutions_not_found"
            ).warning("⚠️ Could not extract total institutions from dataTables_info")
            return 0

        except Exception as e:
            structured_logger.log_error(e, "total_institutions_detection")
            return 0

    async def get_total_pages(self, page: Page) -> int:
        """Get total number of pages with improved detection considering 100 results per page."""
        try:
            # First, set results per page to 100
            await self.set_results_per_page(page, 100)

            # Wait for the page to reload with new pagination
            await page.wait_for_timeout(3000)

            # Now get the total pages with 100 results per page
            await page.wait_for_selector(".paginate_button", timeout=10000)
            paginate_buttons = await page.query_selector_all(".paginate_button")

            max_page = 1
            for button in paginate_buttons:
                text = await button.text_content()
                if text and text.isdigit():
                    page_num = int(text)
                    if page_num > max_page:
                        max_page = page_num

            structured_logger.bind_context(
                action="total_pages_detected",
                total_pages=max_page,
                results_per_page=100,
            ).info(f"📈 Total pages detected with 100 results per page: {max_page}")

            return max_page
        except Exception as e:
            structured_logger.log_error(e, "total_pages_detection")
            return 1

    async def navigate_to_page_robust(self, page: Page, target_page: int) -> bool:
        """Navigate to page with robust error handling using sequential navigation."""
        try:
            # Always set results per page to 100 for efficiency
            if target_page == 1:
                await self.set_results_per_page(page, 100)
                return True

            await page.wait_for_timeout(2000)

            # Always use sequential navigation for reliability
            if target_page > 1:
                current_page = 1
                max_attempts = target_page + 5  # Allow some extra attempts

                structured_logger.bind_context(
                    action="sequential_navigation_start",
                    target_page=target_page,
                ).info(f"🔄 Starting sequential navigation to page {target_page}")

                for attempt in range(max_attempts):
                    if current_page >= target_page:
                        structured_logger.bind_context(
                            action="navigation_success",
                            target_page=target_page,
                            current_page=current_page,
                        ).info(f"✅ Successfully navigated to page {target_page}")
                        return True

                    # Find the "Próximo" button with multiple selectors
                    next_button = None
                    next_selectors = [
                        "a.paginate_button.next:not(.disabled)",
                        "a.next:not(.disabled)",
                        "a[class*='next']:not(.disabled)",
                        "a:contains('Próximo')",
                        "a:contains('Next')",
                    ]

                    for selector in next_selectors:
                        try:
                            next_button = await page.query_selector(selector)
                            if next_button:
                                break
                        except:
                            continue

                    if next_button:
                        try:
                            await next_button.click()
                            await page.wait_for_timeout(3000)  # Increased wait time

                            # Verify we actually moved to the next page
                            try:
                                # Wait for page content to load
                                await page.wait_for_selector(
                                    "#tabelabusca", timeout=10000
                                )
                                current_page += 1

                                structured_logger.bind_context(
                                    action="navigation_step",
                                    current_page=current_page,
                                    target_page=target_page,
                                ).info(f"📄 Navigated to page {current_page}")

                            except Exception as e:
                                structured_logger.bind_context(
                                    action="page_verification_error",
                                    current_page=current_page,
                                    error=str(e),
                                ).warning(
                                    f"⚠️ Page content not loaded after navigation: {e}"
                                )
                                # Don't increment current_page if verification failed

                        except Exception as e:
                            structured_logger.bind_context(
                                action="navigation_click_error",
                                current_page=current_page,
                                error=str(e),
                            ).warning(f"⚠️ Error clicking next button: {e}")
                            break
                    else:
                        structured_logger.bind_context(
                            action="no_next_button",
                            current_page=current_page,
                            target_page=target_page,
                        ).warning(
                            f"⚠️ No 'Próximo' button found on page {current_page}"
                        )
                        break

                structured_logger.bind_context(
                    action="navigation_failed",
                    target_page=target_page,
                    reached_page=current_page,
                ).warning(
                    f"❌ Failed to reach page {target_page}, reached page {current_page}"
                )
                return False

            return True

        except Exception as e:
            structured_logger.log_error(e, f"page_navigation_{target_page}")
            return False

    async def set_results_per_page(self, page: Page, results_per_page: int) -> bool:
        """Set the number of results per page to reduce total pages."""
        try:
            # Wait for the select element to be available
            await page.wait_for_selector(
                "select[name='tabelabusca_length']", timeout=10000
            )

            # Select the option for 100 results per page
            await page.select_option(
                "select[name='tabelabusca_length']", str(results_per_page)
            )

            # Wait for the page to reload with new results
            await page.wait_for_timeout(3000)

            structured_logger.bind_context(
                action="results_per_page_set",
                results_per_page=results_per_page,
            ).info(f"📊 Set results per page to {results_per_page}")

            return True

        except Exception as e:
            structured_logger.bind_context(
                action="set_results_per_page_error",
                results_per_page=results_per_page,
                error=str(e),
            ).warning(f"⚠️ Failed to set results per page to {results_per_page}: {e}")
            return False

    async def extract_school_links(self, page: Page) -> List[str]:
        """Extract school links from current page."""
        try:
            # Wait for the table with a longer timeout and better error handling
            try:
                await page.wait_for_selector("#tabelabusca", timeout=30000)
            except Exception as e:
                structured_logger.bind_context(
                    action="table_not_found", page_num=page.url
                ).warning(
                    f"⚠️ Table #tabelabusca not found on page, trying alternative selectors"
                )

                # Try alternative selectors
                alternative_selectors = [
                    "table tbody tr td a",
                    ".dataTable tbody tr td a",
                    "tbody tr td a",
                ]

                for selector in alternative_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=10000)
                        break
                    except:
                        continue
                else:
                    structured_logger.bind_context(
                        action="no_links_found", page_num=page.url
                    ).warning(f"⚠️ No school links found on page")
                    return []

            await page.wait_for_timeout(3000)

            # Try multiple selectors for school links
            school_links = []
            selectors = [
                "#tabelabusca tbody tr td a",
                "table tbody tr td a",
                ".dataTable tbody tr td a",
            ]

            for selector in selectors:
                try:
                    school_links = await page.query_selector_all(selector)
                    if school_links:
                        break
                except:
                    continue

            links = []

            for link in school_links:
                try:
                    href = await link.get_attribute("href")
                    if href and "DetalhesEscola" in href:
                        # Normalize URL format
                        if href.startswith("/"):
                            href = f"https://transparencia.educacao.sp.gov.br{href}"
                        links.append(href)
                except Exception as e:
                    structured_logger.bind_context(
                        action="link_extraction_error"
                    ).debug(f"⚠️ Error extracting link: {e}")
                    continue

            # Remove duplicates while preserving order
            unique_links = []
            seen = set()
            for link in links:
                if link not in seen:
                    unique_links.append(link)
                    seen.add(link)

            structured_logger.bind_context(
                action="links_extracted",
                total_links=len(links),
                unique_links=len(unique_links),
            ).debug(f"🔗 Extracted {len(unique_links)} unique school links")

            return unique_links

        except Exception as e:
            structured_logger.log_error(e, "link_extraction")
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=lambda retry_state: structured_logger.bind_context(
            action="retry_attempt", attempt=retry_state.attempt_number
        ).warning(
            f"🔄 Retry attempt {retry_state.attempt_number} for school extraction"
        ),
    )
    async def extract_school_details(self, page: Page, detail_url: str) -> dict:
        """Extract school details with retry logic."""
        await page.goto(
            detail_url, wait_until="domcontentloaded", timeout=self.config.timeout
        )
        await page.wait_for_timeout(2000)

        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")

        school_name = ""
        classification = ""
        teaching_directorate = ""
        neighborhood = ""
        municipality = ""
        phone = ""
        email = ""
        ideb_score_final_years = ""
        idesp_score_final_years = ""
        ideb_score_high_school = ""
        idesp_score_high_school = ""
        total_students = ""
        age_06_10_final_years = ""
        age_11_14_final_years = ""
        age_15_17_final_years = ""
        age_18_plus_final_years = ""
        age_06_10_high_school = ""
        age_11_14_high_school = ""
        age_15_17_high_school = ""
        age_18_plus_high_school = ""
        total_classes = ""
        classes_final_years = ""
        classes_high_school = ""
        total_classrooms = ""

        # Find the main content div
        conteudo_div = soup.find("div", class_="conteudo")
        if conteudo_div:
            # Extract school name
            nome_element = conteudo_div.find(
                "h2", class_="escola-titulo", id="nome-escola"
            )
            if nome_element:
                school_name = nome_element.get_text(strip=True)

            # Extract classification
            tag_div = conteudo_div.find("div", class_="tag")
            if tag_div:
                tag_p = tag_div.find("p", class_="tags")
                if tag_p:
                    classification = tag_p.get_text(strip=True)

                    # Extract total students and age range data
            info_alunos_divs = conteudo_div.find_all("div", class_="info-alunos")

            for info_alunos_div in info_alunos_divs:
                alunos_div = info_alunos_div.find("div", class_="alunos")
                if alunos_div:
                    h2_title = alunos_div.find("h2")
                    if h2_title:
                        title_text = h2_title.get_text(strip=True)

                        if title_text == "Alunos":
                            # Extrair total de alunos
                            quantidade_alunos = alunos_div.find(
                                "span", id="quantidade-alunos"
                            )
                            if quantidade_alunos:
                                total_students = quantidade_alunos.get_text(strip=True)

                            # Extrair dados de faixa etária da tabela
                            table = info_alunos_div.find("table")
                            if table:
                                thead = table.find("thead")
                                header_cells = []
                                if thead:
                                    header_row = thead.find("tr")
                                    if header_row:
                                        header_cells = [
                                            th.get_text(strip=True)
                                            for th in header_row.find_all("th")
                                        ]
                                else:
                                    # Se não houver thead, pegar do primeiro tr do tbody
                                    tbody = table.find("tbody")
                                    if tbody:
                                        header_row = tbody.find("tr")
                                        if header_row:
                                            header_cells = [
                                                th.get_text(strip=True)
                                                for th in header_row.find_all("th")
                                            ]
                                # Mapear índices
                                idx_final_years = None
                                idx_high_school = None
                                for idx, col in enumerate(header_cells):
                                    if col.strip().lower().startswith("anos finais"):
                                        idx_final_years = idx
                                    if col.strip().lower().startswith("ensino médio"):
                                        idx_high_school = idx
                                # Pegar linhas de dados
                                tbody = table.find("tbody")
                                if tbody:
                                    rows = (
                                        tbody.find_all("tr")[1:]
                                        if len(tbody.find_all("tr")) > 1
                                        else []
                                    )
                                    for row in rows:
                                        cells = row.find_all("td")
                                        if len(cells) >= 1:
                                            age_range = cells[0].get_text(strip=True)
                                            final_years = (
                                                cells[idx_final_years]
                                                if idx_final_years is not None
                                                and len(cells) > idx_final_years
                                                else None
                                            )
                                            high_school = (
                                                cells[idx_high_school]
                                                if idx_high_school is not None
                                                and len(cells) > idx_high_school
                                                else None
                                            )
                                            final_years_val = (
                                                final_years.get_text(strip=True)
                                                if final_years
                                                else ""
                                            )
                                            high_school_val = (
                                                high_school.get_text(strip=True)
                                                if high_school
                                                else ""
                                            )
                                            if final_years_val == "-":
                                                final_years_val = ""
                                            if high_school_val == "-":
                                                high_school_val = ""
                                            # Mapear para variáveis
                                            if age_range == "06 a 10 anos":
                                                age_06_10_final_years = final_years_val
                                                age_06_10_high_school = high_school_val
                                            elif age_range == "11 a 14 anos":
                                                age_11_14_final_years = final_years_val
                                                age_11_14_high_school = high_school_val
                                            elif age_range == "15 a 17 anos":
                                                age_15_17_final_years = final_years_val
                                                age_15_17_high_school = high_school_val
                                            elif age_range == "acima dos 18 anos":
                                                age_18_plus_final_years = (
                                                    final_years_val
                                                )
                                                age_18_plus_high_school = (
                                                    high_school_val
                                                )

                        elif title_text == "Total de Turmas":
                            # Extrair total de turmas
                            quantidade_alunos = alunos_div.find(
                                "span", id="quantidade-alunos"
                            )
                            if quantidade_alunos:
                                total_classes = quantidade_alunos.get_text(strip=True)
                            # Extrair dados de turmas da tabela
                            table = info_alunos_div.find("table")
                            if table:
                                thead = table.find("thead")
                                header_cells = []
                                if thead:
                                    header_row = thead.find("tr")
                                    if header_row:
                                        header_cells = [
                                            th.get_text(strip=True)
                                            for th in header_row.find_all("th")
                                        ]
                                else:
                                    # Se não houver thead, pegar do primeiro tr do tbody
                                    tbody = table.find("tbody")
                                    if tbody:
                                        header_row = tbody.find("tr")
                                        if header_row:
                                            header_cells = [
                                                th.get_text(strip=True)
                                                for th in header_row.find_all("th")
                                            ]
                                idx_final_years = None
                                idx_high_school = None
                                for idx, col in enumerate(header_cells):
                                    if col.strip().lower().startswith("anos finais"):
                                        idx_final_years = idx
                                    if col.strip().lower().startswith("ensino médio"):
                                        idx_high_school = idx
                                # Pegar linha de dados
                                tbody = table.find("tbody")
                                if tbody:
                                    data_rows = (
                                        tbody.find_all("tr")[1:]
                                        if len(tbody.find_all("tr")) > 1
                                        else []
                                    )
                                    for row in data_rows:
                                        cells = row.find_all("td")
                                        if len(cells) >= 1:
                                            final_years = (
                                                cells[idx_final_years]
                                                if idx_final_years is not None
                                                and len(cells) > idx_final_years
                                                else None
                                            )
                                            high_school = (
                                                cells[idx_high_school]
                                                if idx_high_school is not None
                                                and len(cells) > idx_high_school
                                                else None
                                            )
                                            classes_final_years = (
                                                final_years.get_text(strip=True)
                                                if final_years
                                                else ""
                                            )
                                            classes_high_school = (
                                                high_school.get_text(strip=True)
                                                if high_school
                                                else ""
                                            )

            # Find escola-dados div which contains all the detailed information
            escola_dados = conteudo_div.find("div", class_="escola-dados")
            if escola_dados:
                # Extract teaching directorate
                endereco_escola = escola_dados.find("p", id="endereco-escola")
                if endereco_escola:
                    text = endereco_escola.get_text(strip=True)
                    if "Diretoria de Ensino:" in text:
                        teaching_directorate = text.split("Diretoria de Ensino:")[
                            1
                        ].strip()

                # Extract neighborhood
                bairro_p = escola_dados.find(
                    "p", string=lambda text: text and "Bairro:" in text
                )
                if bairro_p:
                    text = bairro_p.get_text(strip=True)
                    if "Bairro:" in text:
                        neighborhood = text.split("Bairro:")[1].strip()

                # Extract municipality
                municipio_p = escola_dados.find(
                    "p", string=lambda text: text and "Município:" in text
                )
                if municipio_p:
                    text = municipio_p.get_text(strip=True)
                    if "Município:" in text:
                        municipality = text.split("Município:")[1].strip()

                # Extract phone
                telefone_p = escola_dados.find(
                    "p",
                    string=lambda text: text
                    and any(char.isdigit() for char in text)
                    and "(" in text,
                )
                if telefone_p:
                    # Look for phone pattern (XX) XXXXX-XXXX
                    text = telefone_p.get_text(strip=True)
                    import re

                    phone_match = re.search(r"\(\d{2}\)\s*\d{4,5}-?\d{4}", text)
                    if phone_match:
                        phone = phone_match.group()

                # Extract email
                email_p = escola_dados.find(
                    "p", string=lambda text: text and "@" in text
                )
                if email_p:
                    text = email_p.get_text(strip=True)
                    # Extract email using regex
                    import re

                    email_match = re.search(
                        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text
                    )
                    if email_match:
                        email = email_match.group()

            # Extract IDEB and IDESP scores
            # Look for the classificacao div which contains the scores
            classificacao_div = conteudo_div.find("div", class_="classificacao")
            if classificacao_div:
                structured_logger.bind_context(action="classificacao_div_found").debug(
                    "📊 Found classificacao div"
                )
                # Find the ul element containing the scores
                score_ul = classificacao_div.find("ul")
                if score_ul:
                    score_items = score_ul.find_all("li")
                    structured_logger.bind_context(
                        action="score_items_found", count=len(score_items)
                    ).debug(f"📊 Found {len(score_items)} score items")
                    for item in score_items:
                        # Check if this is "Anos finais" (Final Years)
                        title_element = item.find("h2", class_="titulo-classificacao")
                        if title_element:
                            title_text = title_element.get_text(strip=True)
                            structured_logger.bind_context(
                                action="title_found", title=title_text
                            ).debug(f"📊 Found title: {title_text}")

                            if title_text == "Anos finais":
                                structured_logger.bind_context(
                                    action="processing_anos_finais"
                                ).debug("📊 Processing Anos finais scores")
                                # Extract IDEB score for final years
                                ideb_nota = item.find("p", id="ideb-nota")
                                if ideb_nota:
                                    ideb_score_final_years = ideb_nota.get_text(
                                        strip=True
                                    )
                                    # Replace "-" with empty string if no data
                                    if ideb_score_final_years == "-":
                                        ideb_score_final_years = ""
                                    structured_logger.bind_context(
                                        action="ideb_extracted",
                                        score=ideb_score_final_years,
                                    ).debug(
                                        f"📊 IDEB Anos finais: {ideb_score_final_years}"
                                    )

                                # Extract IDESP score for final years
                                idesp_nota = item.find("p", id="idesp-nota")
                                if idesp_nota:
                                    idesp_score_final_years = idesp_nota.get_text(
                                        strip=True
                                    )
                                    # Replace "-" with empty string if no data
                                    if idesp_score_final_years == "-":
                                        idesp_score_final_years = ""
                                    structured_logger.bind_context(
                                        action="idesp_extracted",
                                        score=idesp_score_final_years,
                                    ).debug(
                                        f"📊 IDESP Anos finais: {idesp_score_final_years}"
                                    )

                            elif title_text == "Ensino Médio":
                                # Extract IDEB score for high school
                                ideb_nota = item.find("p", id="ideb-nota")
                                if ideb_nota:
                                    ideb_score_high_school = ideb_nota.get_text(
                                        strip=True
                                    )
                                    # Replace "-" with empty string if no data
                                    if ideb_score_high_school == "-":
                                        ideb_score_high_school = ""

                                # Extract IDESP score for high school
                                idesp_nota = item.find("p", id="idesp-nota")
                                if idesp_nota:
                                    idesp_score_high_school = idesp_nota.get_text(
                                        strip=True
                                    )
                                    # Replace "-" with empty string if no data
                                    if idesp_score_high_school == "-":
                                        idesp_score_high_school = ""

            # Fallback: Look for scores in any ul element if classificacao not found
            if (
                not ideb_score_final_years
                and not idesp_score_final_years
                and not ideb_score_high_school
                and not idesp_score_high_school
            ):
                score_ul = conteudo_div.find("ul")
                if score_ul:
                    score_items = score_ul.find_all("li")
                    for item in score_items:
                        # Check if this is "Anos finais" (Final Years)
                        title_element = item.find("h2", class_="titulo-classificacao")
                        if title_element:
                            title_text = title_element.get_text(strip=True)

                            if title_text == "Anos finais":
                                # Extract IDEB score for final years
                                ideb_nota = item.find("p", id="ideb-nota")
                                if ideb_nota:
                                    ideb_score_final_years = ideb_nota.get_text(
                                        strip=True
                                    )
                                    # Replace "-" with empty string if no data
                                    if ideb_score_final_years == "-":
                                        ideb_score_final_years = ""

                                # Extract IDESP score for final years
                                idesp_nota = item.find("p", id="idesp-nota")
                                if idesp_nota:
                                    idesp_score_final_years = idesp_nota.get_text(
                                        strip=True
                                    )
                                    # Replace "-" with empty string if no data
                                    if idesp_score_final_years == "-":
                                        idesp_score_final_years = ""

                            elif title_text == "Ensino Médio":
                                # Extract IDEB score for high school
                                ideb_nota = item.find("p", id="ideb-nota")
                                if ideb_nota:
                                    ideb_score_high_school = ideb_nota.get_text(
                                        strip=True
                                    )
                                    # Replace "-" with empty string if no data
                                    if ideb_score_high_school == "-":
                                        ideb_score_high_school = ""

                                # Extract IDESP score for high school
                                idesp_nota = item.find("p", id="idesp-nota")
                                if idesp_nota:
                                    idesp_score_high_school = idesp_nota.get_text(
                                        strip=True
                                    )
                                    # Replace "-" with empty string if no data
                                    if idesp_score_high_school == "-":
                                        idesp_score_high_school = ""

            # Fallback extraction for total students if info-alunos not found
            if not total_students:
                alunos_div = conteudo_div.find("div", class_="alunos")
                if alunos_div:
                    quantidade_alunos = alunos_div.find("span", id="quantidade-alunos")
                    if quantidade_alunos:
                        total_students = quantidade_alunos.get_text(strip=True)

            # Extract total classrooms from infrastructure section
            infraestrutura_escola = conteudo_div.find(
                "div", class_="infraestrutura-escola"
            )
            if infraestrutura_escola:
                infraestrutura_div = infraestrutura_escola.find(
                    "div", class_="infraestrutura"
                )
                if infraestrutura_div:
                    boxes = infraestrutura_div.find_all("div", class_="box")
                    for box in boxes:
                        titulo_div = box.find("div", class_="titulo")
                        if titulo_div:
                            titulo_b = titulo_div.find("b", id="tituloInfraestrutura")
                            if (
                                titulo_b
                                and titulo_b.get_text(strip=True) == "Salas de Aula"
                            ):
                                inf_div = box.find("div", class_="inf")
                                if inf_div:
                                    ul = inf_div.find("ul")
                                    if ul:
                                        li = ul.find("li")
                                        if li:
                                            numero_span = li.find(
                                                "span", id="numeroInfraestrutura"
                                            )
                                            if numero_span:
                                                total_classrooms = numero_span.get_text(
                                                    strip=True
                                                )

            # Fallback extraction if escola-dados not found
            if not teaching_directorate or not neighborhood or not municipality:
                # Look for information in all paragraphs
                all_paragraphs = conteudo_div.find_all("p")
                for p in all_paragraphs:
                    text = p.get_text(strip=True)

                    # Extract teaching directorate
                    if "Diretoria de Ensino:" in text and not teaching_directorate:
                        teaching_directorate = text.split("Diretoria de Ensino:")[
                            1
                        ].strip()

                    # Extract neighborhood
                    elif "Bairro:" in text and not neighborhood:
                        neighborhood = text.split("Bairro:")[1].strip()

                    # Extract municipality
                    elif "Município:" in text and not municipality:
                        municipality = text.split("Município:")[1].strip()

                    # Extract phone (look for pattern)
                    elif (
                        "(" in text
                        and ")" in text
                        and any(char.isdigit() for char in text)
                        and not phone
                    ):
                        import re

                        phone_match = re.search(r"\(\d{2}\)\s*\d{4,5}-?\d{4}", text)
                        if phone_match:
                            phone = phone_match.group()

                    # Extract email
                    elif "@" in text and not email:
                        import re

                        email_match = re.search(
                            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text
                        )
                        if email_match:
                            email = email_match.group()

        # Log extracted student, class and infrastructure data for debugging
        structured_logger.bind_context(
            action="student_data_extracted",
            school_name=school_name,
            total_students=total_students,
            total_classes=total_classes,
            classes_final_years=classes_final_years,
            classes_high_school=classes_high_school,
            total_classrooms=total_classrooms,
            age_06_10_final_years=age_06_10_final_years,
            age_11_14_final_years=age_11_14_final_years,
            age_15_17_final_years=age_15_17_final_years,
            age_18_plus_final_years=age_18_plus_final_years,
            age_06_10_high_school=age_06_10_high_school,
            age_11_14_high_school=age_11_14_high_school,
            age_15_17_high_school=age_15_17_high_school,
            age_18_plus_high_school=age_18_plus_high_school,
        ).debug(
            f"📊 Extracted student, class and infrastructure data for {school_name}"
        )

        return {
            "name": school_name,
            "classification": classification,
            "detail_url": detail_url,
            "teaching_directorate": teaching_directorate,
            "neighborhood": neighborhood,
            "municipality": municipality,
            "phone": phone,
            "email": email,
            "ideb_score_final_years": ideb_score_final_years,
            "idesp_score_final_years": idesp_score_final_years,
            "ideb_score_high_school": ideb_score_high_school,
            "idesp_score_high_school": idesp_score_high_school,
            "total_students": total_students,
            "total_classes": total_classes,
            "classes_final_years": classes_final_years,
            "classes_high_school": classes_high_school,
            "total_classrooms": total_classrooms,
            "age_06_10_final_years": age_06_10_final_years,
            "age_11_14_final_years": age_11_14_final_years,
            "age_15_17_final_years": age_15_17_final_years,
            "age_18_plus_final_years": age_18_plus_final_years,
            "age_06_10_high_school": age_06_10_high_school,
            "age_11_14_high_school": age_11_14_high_school,
            "age_15_17_high_school": age_15_17_high_school,
            "age_18_plus_high_school": age_18_plus_high_school,
        }

    async def process_school_parallel(
        self, context: BrowserContext, url: str, school_num: int, total_schools: int
    ) -> dict:
        """Process a single school in parallel."""
        async with self.semaphore:
            page = await context.new_page()
            try:
                structured_logger.bind_context(
                    action="school_processing",
                    school_num=school_num,
                    total_schools=total_schools,
                    url=url,
                ).info(f"🏫 Processing school {school_num}/{total_schools}")

                school_data = await self.extract_school_details(page, url)
                await asyncio.sleep(self.config.delay_between_requests)

                return school_data
            finally:
                await page.close()

    async def process_page_parallel(
        self, page_num: int, context: BrowserContext
    ) -> List[dict]:
        """Process a single page in parallel."""
        page = await context.new_page()
        page_results = []

        try:
            # Navigate to the page with better error handling
            try:
                await page.goto(
                    self.config.base_url,
                    wait_until="domcontentloaded",
                    timeout=self.config.timeout,
                )
                await page.wait_for_timeout(5000)
            except Exception as e:
                structured_logger.bind_context(
                    action="page_navigation_error", page_num=page_num
                ).warning(f"⚠️ Error navigating to base URL: {e}")
                return []

            # Set results per page to 100 for efficiency
            try:
                await self.set_results_per_page(page, 100)
            except Exception as e:
                structured_logger.bind_context(
                    action="set_results_per_page_error", page_num=page_num
                ).warning(f"⚠️ Error setting results per page: {e}")

            # Navigate to specific page if needed
            if page_num > 1:
                try:
                    if not await self.navigate_to_page_robust(page, page_num):
                        structured_logger.bind_context(
                            action="navigation_failed", page_num=page_num
                        ).warning(f"⚠️ Could not navigate to page {page_num}")
                        return []
                except Exception as e:
                    structured_logger.bind_context(
                        action="page_navigation_error", page_num=page_num
                    ).warning(f"⚠️ Error navigating to page {page_num}: {e}")
                    return []

            # Extract school links
            try:
                school_links = await self.extract_school_links(page)
            except Exception as e:
                structured_logger.bind_context(
                    action="link_extraction_error", page_num=page_num
                ).warning(f"⚠️ Error extracting links from page {page_num}: {e}")
                return []

            structured_logger.bind_context(
                action="page_processing",
                page_num=page_num,
                schools_found=len(school_links),
            ).info(f"📄 Page {page_num}: Found {len(school_links)} unique schools")

            if school_links:
                # Process schools in parallel with better error handling
                tasks = []
                for i, link in enumerate(school_links):
                    task = self.process_school_parallel(
                        context, link, i + 1, len(school_links)
                    )
                    tasks.append(task)

                if tasks:
                    try:
                        results = await asyncio.gather(*tasks, return_exceptions=True)

                        for result in results:
                            if isinstance(result, dict):
                                page_results.append(result)
                            elif isinstance(result, Exception):
                                structured_logger.bind_context(
                                    action="school_processing_error"
                                ).warning(f"⚠️ Error processing school: {result}")
                    except Exception as e:
                        structured_logger.bind_context(
                            action="parallel_processing_error", page_num=page_num
                        ).warning(
                            f"⚠️ Error in parallel processing for page {page_num}: {e}"
                        )

        except Exception as e:
            structured_logger.log_error(e, f"page_processing_{page_num}")

        finally:
            try:
                await page.close()
            except:
                pass

        return page_results
