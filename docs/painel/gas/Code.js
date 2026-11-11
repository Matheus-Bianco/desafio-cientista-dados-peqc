/**
 * Painel de Gestao Educacional - RMI (web app Apps Script).
 *
 * O painel e um HTML autocontido (Index.html) com os dados ja embutidos
 * (agregados anonimizados dos marts dbt/BigQuery). Nao le planilha nem API:
 * o GAS serve apenas como hospedagem do web app, com link publico.
 */
function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('Painel de Gestao Educacional - RMI')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}
