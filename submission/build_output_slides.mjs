// A short, editable companion to the capstone deck, using one recorded run.
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { FileBlob, Presentation, PresentationFile } from '@oai/artifact-tool';
const root=process.env.PAP_REPO_ROOT, input=process.env.PAP_OUTPUT_EXAMPLE;
const out=process.env.PAP_SUBMISSION_OUT, build=process.env.PAP_SUBMISSION_BUILD;
const skill=process.env.PAP_PRESENTATIONS_SKILL;
const evidencePath=path.relative(root,path.join(input,'output-example.json'));
const example=JSON.parse(await fs.readFile(path.join(input,'output-example.json'),'utf8'));
const publication=example.publication, rows=publication.profile.intervals;
if(publication.status!=='valid' || rows.length!==12) throw new Error('Expected one valid twelve-hour publication');
const total=rows.reduce((sum,row)=>sum+row.energy_kwh,0).toFixed(3);
const first=String(rows[0].available_kw), confidence=publication.profile.confidence;
const guidance=publication.search?.guidance?.summary || publication.interpretation?.advice?.explanation || 'The linear workflow published the calculated solar-surplus profile.';
const telemetry=publication.evidence.telemetry;
const {finalizePresentation,resolvePresentationFont,applyPresentationChartFont}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const font=resolvePresentationFont({fontFamily:'Arial'});
const C={bg:'#0B1823',white:'#F2F7FA',cyan:'#82D4E5',muted:'#B4C9D5',amber:'#E8B362',edge:'#436374'};
const pres=Presentation.create({slideSize:{width:1280,height:720}});
function text(s,value,x,y,w,h,size=25,color=C.white,bold=false){
  const box=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  box.text=value;
  box.text.style={typeface:font,fontSize:size,color,bold,verticalAlignment:'top',autoFit:'none',wrap:'square',insets:{left:0,right:0,top:0,bottom:0}};
  return box;
}
function slide(title,index,notes){
  const s=pres.slides.add();s.background.fill=C.bg;
  text(s,'DragonWings PAP / output walkthrough',64,32,1100,25,17,C.cyan);
  text(s,title,64,78,1152,94,43,C.white,true);
  text(s,`${index} / 3`,1150,684,70,24,15,C.muted);
  s.speakerNotes.textFrame.setText(`${notes}\n\nEvidence: ${evidencePath}. Episode ${publication.episode_id}. Captured ${example.captured_at}. Source scrape ${telemetry.observed_at}. Real MySolArk telemetry with synthetic weather. UI screenshot from the same episode. Repository: https://github.com/roboyak/PAP-Agent (owner controls visibility).`);
  return s;
}
{
  const s=slide('The output an operator sees',1,`Show the completed Forecast page. The first interval allocates ${first} kW beyond existing load. Across twelve one-hour intervals the model allocates ${total} kWh. Confidence is ${confidence}. These are saved evaluation results, not hardware commands. The separate Inspector opens the same episode.`);
  s.images.add({blob:await fs.readFile(path.join(input,'output-panel.png')),contentType:'image/png',alt:'Actual Forecast output for the recorded MySolArk run',fit:'contain',position:{left:64,top:175,width:760,height:415}});
  text(s,`${first} kW`,869,183,347,75,56,C.cyan,true);
  text(s,'Additional power in the first hour',869,265,347,70,26);
  text(s,`${total} kWh`,869,358,347,69,45,C.amber,true);
  text(s,'Energy across twelve hours',869,432,347,66,26);
  text(s,`${confidence[0].toUpperCase()+confidence.slice(1)} confidence`,869,528,347,45,29,C.muted);
  text(s,'What it does',64,615,500,25,18,C.cyan,true);
  text(s,'Turns source readings into an hourly power profile.',64,649,690,42,24);
  text(s,'Why it matters',805,615,400,25,18,C.amber,true);
  text(s,'Makes the result easy to review.',805,649,380,60,24);
}
{
  const s=slide('How to read the twelve-hour profile',2,`The bars are the exact published available_kw values. Each covers one hour. The kWh total is the sum of energy_kwh from those intervals. Zero means no extra solar allocation. The total does not describe a continuous load or energy available all at once. This is a synthetic-weather persistence baseline; the taper is not a validated overnight solar forecast.`);
  text(s,'Additional power (kW)',64,175,900,32,23,C.cyan);
  const chart=s.charts.add('bar',{
    position:{left:64,top:215,width:1152,height:327},
    categories:rows.map(row=>row.starts_at.slice(11,16)),
    series:[{name:'Additional power (kW)',values:rows.map(row=>row.available_kw),fill:C.cyan,valuesFormatCode:'0.000'}],
    barOptions:{direction:'column',grouping:'clustered',gapWidth:70},hasLegend:false,
    xAxis:{textStyle:{typeface:font,fontSize:17,fill:C.muted},line:{fill:C.edge,width:1},majorGridlines:null},
    yAxis:{min:0,numberFormatCode:'0.00',textStyle:{typeface:font,fontSize:17,fill:C.muted},line:{fill:'none',width:0},majorGridlines:{fill:C.edge,width:1}},
    dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:font,fontSize:18,fill:C.white}},
    chartFill:C.bg,plotAreaFill:C.bg,chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0}
  });
  applyPresentationChartFont(chart,{fontFamily:font});
  text(s,`${rows[0].starts_at.replace('T',' ').slice(0,16)} to ${rows.at(-1).ends_at.replace('T',' ').slice(0,16)} UTC`,64,554,1152,28,18,C.muted);
  text(s,`${total} kWh in total`,64,610,520,45,31,C.amber,true);
  text(s,'Zero means no additional solar allocation.\nThe total is spread across the forecast.',630,608,570,74,26);
}
{
  const s=slide('Guidance, evidence and human review',3,`Read the model guidance verbatim. The publication's status means deterministic checks passed. Confidence is qualitative. Real solar and load readings are used with synthetic weather, constant demand and zero battery discharge. Inspect this run opens the matching episode. Trace gives workflow order; Context, Memory, Tools, Subagent and Health explain its evidence, model activity and current dependencies. The operator retains control.`);
  text(s,'Recorded model guidance',64,173,1152,28,18,C.muted);
  text(s,guidance,64,218,1152,105,36,C.cyan,true);
  text(s,'What supports the result',64,334,535,43,29,C.white,true);
  text(s,`${telemetry.solar_power_kw} kW measured solar\n${telemetry.load_power_kw} kW measured load\n${telemetry.battery_voltage_v} V battery / ${publication.evidence.policy.min_battery_voltage_v} V floor`,64,396,540,151,27);
  text(s,'What still needs judgment',680,334,535,43,29,C.amber,true);
  text(s,'Synthetic weather and constant demand\nNo battery discharge or equipment commands\nForecast accuracy remains unproven',680,396,535,151,26);
  text(s,'Inspect this run',64,590,500,38,27,C.cyan,true);
  text(s,'Saved details share one episode. Health checks the current service.',64,634,1130,43,27);
}
await fs.mkdir(build,{recursive:true});await fs.mkdir(out,{recursive:true});
const candidatePath=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(pres)).save(candidatePath);
const finalPath=path.join(out,'DragonWings_Output_Walkthrough.pptx');
await finalizePresentation({workspaceDir:root,candidatePath,finalPath,pythonExecutable:process.env.RUNTIME_PYTHON,
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
  explicitTotalSlideCount:3,requiredNativeChartOwnerSlides:[2],materializeLiteralChartWorkbooks:true,
  fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
const deck=await PresentationFile.importPptx(await FileBlob.load(finalPath));
for(let i=0;i<deck.slides.items.length;i++){
  const png=await deck.export({slide:deck.slides.items[i],format:'png',scale:2});
  await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));
}
console.log(finalPath);
