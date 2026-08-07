from playwright.async_api import Page

class BasePage:
    """Classe base para o padrão Page Object Model em testes locais."""
    def __init__(self, page: Page):
        self.page = page

    async def navigate_to(self, url: str):
        await self.page.goto(url, wait_until="networkidle")

    async def fill_field(self, selector: str, value: str):
        await self.page.wait_for_selector(selector)
        await self.page.fill(selector, value)

    async def click_element(self, selector: str):
        await self.page.wait_for_selector(selector)
        await self.page.click(selector)
