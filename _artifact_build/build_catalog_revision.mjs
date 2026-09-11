import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "C:/Users/Professional/Desktop/ASOTIA/asotia/outputs/catalog-revision";
const outputPath = `${outputDir}/asotia_catalog_revision.xlsx`;
const navy = "#162019";
const gold = "#E0B36B";
const paleGold = "#FFF2D7";
const green = "#DDEAD6";
const border = "#CBD3C9";
const font = "Arial";

const workbook = Workbook.create();
const revision = workbook.worksheets.add("Ревизия товаров");
const filters = workbook.worksheets.add("Фильтры");
const collections = workbook.worksheets.add("Подборки");

for (const sheet of [revision, filters, collections]) {
  sheet.showGridLines = false;
  sheet.getRange("A1:Z200").format.font = { name: font, size: 10, color: "#1C241D" };
}

revision.mergeCells("A1:Y1");
revision.getRange("A1").values = [["Asotia Food Shop — ревизия каталога"]];
revision.getRange("A1:Y1").format = {
  fill: navy,
  font: { name: font, size: 16, bold: true, color: "#FFFFFF" },
  verticalAlignment: "center",
};
revision.getRange("A1:Y1").format.rowHeight = 30;
revision.mergeCells("A2:Y2");
revision.getRange("A2").values = [["Одна строка — один товар. Для нового товара оставьте ID пустым. Жёлтые ячейки заполняйте в цеху; текущие значения можно заменить."]];
revision.getRange("A2:Y2").format = { font: { name: font, italic: true, color: "#59655B" }, wrapText: true };
revision.getRange("A2:Y2").format.rowHeight = 28;
revision.getRange("A3:Y3").merge();
revision.getRange("A3").values = [["Логика характеристик: несколько значений одной характеристики дают OR; разные характеристики — AND. Фото: запишите точное имя будущего файла, например products/тушёнка-говяжья.jpg."]];
revision.getRange("A3:Y3").format = { font: { name: font, italic: true, color: "#59655B" }, wrapText: true };
revision.getRange("A3:Y3").format.rowHeight = 28;

const revisionHeaders = [[
  "Действие", "ID текущего товара", "Категория", "Название", "Слаг", "Короткое описание", "Полное описание / состав", "Цена, ₽", "Старая цена, ₽", "Остаток, шт.", "Вес, г", "Объём, мл", "Кол-во единиц, шт.", "Вид продукции", "Состав", "Основной ингредиент", "Упаковка", "Особенности", "Фото: имя файла", "Фото снято", "Активен", "Новинка", "Комментарий", "Проверил", "Дата проверки"
]];
revision.getRange("A5:Y5").values = revisionHeaders;
revision.getRange("A5:Y5").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, wrapText: true, verticalAlignment: "center", horizontalAlignment: "center", borders: { preset: "all", style: "thin", color: "#FFFFFF" } };
revision.getRange("A5:Y5").format.rowHeight = 42;

const sampleRows = [
  ["Проверить", 65, "Консервы", "Говядина", "говядина", "Банка 0,5 л", "", 480, null, 195, null, 500, 1, "Тушёнка", "Мясо", "Говядина", "Стеклянная банка", "", "products/говядина-1.jpg", "Нет", "Да", "Нет", "Уточнить вес в граммах и описание", "", null],
  ["Проверить", 84, "Консервы", "Гречка с говядиной", "гречка-с-говядиной", "", "", 320, null, 110, null, null, 1, "Готовое блюдо", "Мясо", "Говядина", "", "", "products/гречка-с-говядиной.jpg", "Нет", "Да", "Нет", "Уточнить вес, упаковку и состав", "", null],
  ["Новый", null, "", "", "", "", "", null, null, null, null, null, null, "", "", "", "", "", "", "Нет", "Да", "Нет", "", "", null],
];
const rowCount = 80;
const rows = [...sampleRows, ...Array.from({ length: rowCount - sampleRows.length }, () => Array(25).fill(null))];
revision.getRange(`A6:Y${5 + rowCount}`).values = rows;
revision.getRange(`A6:Y${5 + rowCount}`).format.borders = { preset: "insideHorizontal", style: "thin", color: border };
revision.getRange(`A6:Y${5 + rowCount}`).format.verticalAlignment = "center";
revision.getRange(`A6:Y${5 + rowCount}`).format.wrapText = true;
revision.getRange(`A6:Y${5 + rowCount}`).format.rowHeight = 24;
revision.getRange(`A6:Y${5 + rowCount}`).format.fill = paleGold;
revision.getRange("B6:B7").format.fill = green;
revision.getRange("C6:D7").format.fill = green;
revision.getRange("H6:J7").format.fill = green;
revision.getRange("N6:S7").format.fill = green;
revision.getRange("U6:V7").format.fill = green;
revision.getRange(`H6:I${5 + rowCount}`).format.numberFormat = "#,##0.00";
revision.getRange(`J6:M${5 + rowCount}`).format.numberFormat = "#,##0";
revision.getRange(`Y6:Y${5 + rowCount}`).format.numberFormat = "dd.mm.yyyy";
revision.getRange(`A6:A${5 + rowCount}`).dataValidation = { rule: { type: "list", values: ["Проверить", "Новый", "Обновить", "Снять с витрины"] } };
revision.getRange(`C6:C${5 + rowCount}`).dataValidation = { rule: { type: "list", values: ["Консервы", "Заморозка", "Другое"] } };
for (const col of ["T", "U", "V"]) {
  revision.getRange(`${col}6:${col}${5 + rowCount}`).dataValidation = { rule: { type: "list", values: ["Да", "Нет"] } };
}
revision.tables.add(`A5:Y${5 + rowCount}`, true, "CatalogRevision");
revision.freezePanes.freezeRows(5);

const widths = [14, 16, 15, 25, 22, 28, 34, 12, 14, 13, 10, 12, 16, 18, 16, 22, 20, 18, 31, 12, 10, 10, 30, 16, 15];
widths.forEach((width, index) => { revision.getRangeByIndexes(0, index, 1, 1).format.columnWidth = width; });

filters.mergeCells("A1:F1");
filters.getRange("A1").values = [["Настройка фильтров каталога"]];
filters.getRange("A1:F1").format = { fill: navy, font: { name: font, size: 16, bold: true, color: "#FFFFFF" }, verticalAlignment: "center" };
filters.getRange("A1:F1").format.rowHeight = 30;
filters.mergeCells("A2:F2");
filters.getRange("A2").values = [["Оставляйте активными только понятные покупателю значения, которые есть хотя бы у одного товара. Порядок меньше — выше в фильтре."]];
filters.getRange("A2:F2").format = { font: { name: font, italic: true, color: "#59655B" }, wrapText: true };
filters.getRange("A2:F2").format.rowHeight = 28;
filters.getRange("A4:F4").values = [["Характеристика", "Значение", "Активно", "Порядок", "Использовать в фильтрах", "Примечание"]];
filters.getRange("A4:F4").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", borders: { preset: "all", style: "thin", color: "#FFFFFF" } };
const filterRows = [
  ["Вид продукции", "Тушёнка", "Да", 10, "Да", ""], ["Вид продукции", "Паштет", "Да", 20, "Да", ""], ["Вид продукции", "Рыбный продукт", "Да", 30, "Да", ""], ["Вид продукции", "Овощная консерва", "Да", 40, "Да", ""], ["Вид продукции", "Готовое блюдо", "Да", 50, "Да", ""], ["Вид продукции", "Полуфабрикат", "Да", 60, "Да", ""], ["Вид продукции", "Фарш", "Да", 70, "Да", ""], ["Вид продукции", "Соус", "Да", 80, "Да", ""], ["Вид продукции", "Компот", "Да", 90, "Да", ""], ["Вид продукции", "Варенье", "Да", 100, "Да", ""],
  ["Состав", "Мясо", "Да", 10, "Да", ""], ["Состав", "Птица", "Да", 20, "Да", ""], ["Состав", "Рыба", "Да", 30, "Да", ""], ["Состав", "Морепродукты", "Да", 40, "Да", ""], ["Состав", "Овощи", "Да", 50, "Да", ""], ["Состав", "Фрукты", "Да", 60, "Да", ""], ["Состав", "Молочная продукция", "Да", 70, "Да", ""],
  ["Основной ингредиент", "Говядина", "Да", 10, "Да", ""], ["Основной ингредиент", "Свинина", "Да", 20, "Да", ""], ["Основной ингредиент", "Курица", "Да", 30, "Да", ""], ["Основной ингредиент", "Индейка", "Да", 40, "Да", ""], ["Основной ингредиент", "Баранина", "Да", 50, "Да", ""], ["Основной ингредиент", "Конина", "Да", 60, "Да", ""], ["Основной ингредиент", "Утка", "Да", 70, "Да", ""], ["Основной ингредиент", "Тунец", "Да", 80, "Да", ""], ["Основной ингредиент", "Минтай", "Да", 90, "Да", ""], ["Основной ингредиент", "Треска", "Да", 100, "Да", ""], ["Основной ингредиент", "Кальмар", "Да", 110, "Да", ""],
  ["Упаковка", "Стеклянная банка", "Да", 10, "Да", ""], ["Упаковка", "Жестяная банка", "Да", 20, "Да", ""], ["Упаковка", "Бутылка", "Да", 30, "Да", ""], ["Упаковка", "Вакуум", "Да", 40, "Да", ""], ["Особенности", "Без мяса", "Да", 10, "Да", "Назначать только при явном подтверждении"],
];
filters.getRange(`A5:F${4 + filterRows.length}`).values = filterRows;
filters.getRange(`A5:F${4 + filterRows.length}`).format = { fill: paleGold, borders: { preset: "insideHorizontal", style: "thin", color: border }, verticalAlignment: "center" };
filters.getRange(`C5:C${4 + filterRows.length}`).dataValidation = { rule: { type: "list", values: ["Да", "Нет"] } };
filters.getRange(`E5:E${4 + filterRows.length}`).dataValidation = { rule: { type: "list", values: ["Да", "Нет"] } };
filters.tables.add(`A4:F${4 + filterRows.length}`, true, "CatalogFilters");
filters.freezePanes.freezeRows(4);
[18, 24, 12, 11, 24, 40].forEach((width, index) => { filters.getRangeByIndexes(0, index, 1, 1).format.columnWidth = width; });

collections.mergeCells("A1:G1");
collections.getRange("A1").values = [["Подборки для главной страницы"]];
collections.getRange("A1:G1").format = { fill: navy, font: { name: font, size: 16, bold: true, color: "#FFFFFF" }, verticalAlignment: "center" };
collections.getRange("A1:G1").format.rowHeight = 30;
collections.mergeCells("A2:G2");
collections.getRange("A2").values = [["Категории в одной ячейке перечисляйте через запятую: это OR. В правилах: значения одной характеристики через запятую — OR; разные характеристики через точку с запятой — AND."]];
collections.getRange("A2:G2").format = { font: { name: font, italic: true, color: "#59655B" }, wrapText: true };
collections.getRange("A2:G2").format.rowHeight = 32;
collections.getRange("A4:G4").values = [["Название подборки", "Описание на главной", "Категории", "Правила по характеристикам", "Порядок", "Активна", "Комментарий"]];
collections.getRange("A4:G4").format = { fill: navy, font: { name: font, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", wrapText: true, borders: { preset: "all", style: "thin", color: "#FFFFFF" } };
const collectionRows = [
  ["Готовые блюда", "Ужин без долгой готовки — разогреть и подать.", "Консервы", "Вид продукции=Готовое блюдо", 10, "Да", ""],
  ["Тушёнка", "Плотный запас для домашнего стола.", "Консервы", "Вид продукции=Тушёнка", 20, "Да", ""],
  ["Птица", "Курица, индейка и утка для разных рецептов.", "", "Основной ингредиент=Курица, Индейка, Утка", 30, "Да", ""],
  ["Заморозка", "Практичные продукты, когда нужно приготовить быстро.", "Заморозка", "", 40, "Да", ""],
  ...Array.from({ length: 16 }, () => Array(7).fill(null)),
];
collections.getRange(`A5:G${4 + collectionRows.length}`).values = collectionRows;
collections.getRange(`A5:G${4 + collectionRows.length}`).format = { fill: paleGold, borders: { preset: "insideHorizontal", style: "thin", color: border }, verticalAlignment: "center", wrapText: true };
collections.getRange(`F5:F${4 + collectionRows.length}`).dataValidation = { rule: { type: "list", values: ["Да", "Нет"] } };
collections.tables.add(`A4:G${4 + collectionRows.length}`, true, "HomeCollections");
collections.freezePanes.freezeRows(4);
[24, 40, 22, 48, 11, 11, 36].forEach((width, index) => { collections.getRangeByIndexes(0, index, 1, 1).format.columnWidth = width; });

workbook.recalculate();
await fs.mkdir(outputDir, { recursive: true });
const preview = await workbook.render({ sheetName: "Ревизия товаров", range: "A1:Y18", scale: 1.2, format: "png" });
await fs.writeFile(`${outputDir}/catalog_revision_preview.png`, new Uint8Array(await preview.arrayBuffer()));
const filtersPreview = await workbook.render({ sheetName: "Фильтры", range: "A1:F38", scale: 1.2, format: "png" });
await fs.writeFile(`${outputDir}/catalog_filters_preview.png`, new Uint8Array(await filtersPreview.arrayBuffer()));
const collectionsPreview = await workbook.render({ sheetName: "Подборки", range: "A1:G16", scale: 1.2, format: "png" });
await fs.writeFile(`${outputDir}/catalog_collections_preview.png`, new Uint8Array(await collectionsPreview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(outputPath);
