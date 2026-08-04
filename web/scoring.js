export const MARK_NAMES = ["flagged", "sensitive", "follow_up", "used"];
export const COMPONENT_MAX = {evidence_review:10,evidence_marking:20,confidence:15,corroboration:10,authenticity:10,release:15,actions:15,timeliness:5};
export const roundHalfAway = value => Math.floor(Number(value) + 0.5);
export function expectedMarks(scenario){return Object.fromEntries(scenario.evidence_cards.map(card=>[card.id,Object.fromEntries(MARK_NAMES.map(name=>[name,Boolean(card.expected_marks[name])]))]));}
export function markingDiagnostics(scenario,marks){
  const result={};
  for(const name of MARK_NAMES){let tp=0,tn=0,fp=0,fn=0;
    for(const card of scenario.evidence_cards){const expected=Boolean(card.expected_marks[name]); const actual=Boolean(marks?.[card.id]?.[name]);
      if(expected&&actual)tp++; else if(expected&&!actual)fn++; else if(!expected&&actual)fp++; else tn++;}
    const positives=tp+fn, negatives=tn+fp; if(!positives||!negatives) throw new Error(`Mark category ${name} must contain positive and negative examples`);
    const recall=tp/positives, specificity=tn/negatives, precision=(tp+fp)?tp/(tp+fp):0, chance_corrected_skill=Math.max(0,recall+specificity-1);
    result[name]={tp,tn,fp,fn,precision,recall,specificity,chance_corrected_skill};
  } return result;
}
export function markingScore(scenario,marks){const d=markingDiagnostics(scenario,marks); const vals=Object.values(d); return roundHalfAway(20*vals.reduce((a,v)=>a+v.chance_corrected_skill,0)/vals.length);}
export function evidenceReviewScore(scenario,count){return scenario.evidence_cards.length?roundHalfAway(10*count/scenario.evidence_cards.length):0;}
export function categoricalScore(choice,correct,unsafe,maximum){if(correct.includes(choice))return maximum;if(unsafe.includes(choice))return 0;return Math.floor(maximum/2);}
export const confidenceScore=(s,c)=>categoricalScore(c,s.correct_confidence_range,s.unsafe_choices,15);
export const corroborationScore=(s,c)=>categoricalScore(c,s.correct_corroboration_range,s.unsafe_corroboration_choices,10);
export const authenticityScore=(s,c)=>categoricalScore(c,s.correct_authenticity_range,s.unsafe_authenticity_choices,10);
export function releaseScore(s,id){const x=s.release_options.find(o=>o.id===id);return x?Math.max(0,Math.min(15,Number(x.doctrine_score))):0;}
export function actionCosts(s,actions){const r={time:0,authority:0};for(const [name,on] of Object.entries(actions||{})){if(on&&s.action_costs[name]){r.time+=Number(s.action_costs[name].time);r.authority+=Number(s.action_costs[name].authority);}}return r;}
export function actionPlanValid(s,actions){const c=actionCosts(s,actions),b=s.action_budget;return c.time<=Number(b.time)&&c.authority<=Number(b.authority);}
export function actionsScore(s,actions){if(!actionPlanValid(s,actions))throw new Error('Action plan exceeds time or authority budget');let p=0;for(const [n,v] of Object.entries(s.action_scores)){if(actions?.[n])p+=Number(v);}return Math.max(0,Math.min(15,p));}
export function timelinessScore(minutes){return minutes>=10?5:minutes>=5?4:minutes>0?2:0;}
export function scoreBreakdown(s,d){if(!d.human_confirmation)throw new Error('Human final confirmation is required');if(d.reviewed_count<s.evidence_cards.length)throw new Error('Complete evidence review is required');if(!actionPlanValid(s,d.actions))throw new Error('Action plan exceeds time or authority budget');return {evidence_review:evidenceReviewScore(s,d.reviewed_count),evidence_marking:markingScore(s,d.marks),confidence:confidenceScore(s,d.confidence),corroboration:corroborationScore(s,d.corroboration),authenticity:authenticityScore(s,d.authenticity),release:releaseScore(s,d.release_id),actions:actionsScore(s,d.actions),timeliness:timelinessScore(d.remaining_minutes)};}
export function excellentGate(s,d,rubric){const b=scoreBreakdown(s,d);const gate=rubric.excellent_gate||{};return b.evidence_marking>=Number(gate.minimum_evidence_marking)&&b.actions>=Number(gate.minimum_action_score||0)&&s.correct_confidence_range.includes(d.confidence)&&s.correct_corroboration_range.includes(d.corroboration)&&s.correct_authenticity_range.includes(d.authenticity)&&releaseScore(s,d.release_id)===15&&actionPlanValid(s,d.actions)&&(s.critical_safeguards||[]).every(name=>Boolean(d.actions?.[name]));}
export function credibleGate(s,d,rubric){return scoreBreakdown(s,d).evidence_marking>=Number(rubric.credible_gate.minimum_evidence_marking);}
export function totalScore(s,d,rubric){const raw=Object.values(scoreBreakdown(s,d)).reduce((a,b)=>a+b,0);if(raw>=75&&!credibleGate(s,d,rubric))return 74;if(raw>=90&&!excellentGate(s,d,rubric))return 89;return raw;}
export function performanceLabel(s,d,rubric){const score=totalScore(s,d,rubric);if(score>=90&&excellentGate(s,d,rubric))return 'Strong doctrine alignment';if(score>=75)return 'Bounded crisis handling';if(score>=60)return 'Mixed doctrine alignment';return 'High governance risk';}
export function canonicalJson(value){if(Array.isArray(value))return `[${value.map(canonicalJson).join(',')}]`;if(value&&typeof value==='object'){return `{${Object.keys(value).sort().map(k=>`${JSON.stringify(k)}:${canonicalJson(value[k])}`).join(',')}}`;}return JSON.stringify(value);}
export async function sha256Hex(text){const bytes=new TextEncoder().encode(text);const hash=await crypto.subtle.digest('SHA-256',bytes);return [...new Uint8Array(hash)].map(b=>b.toString(16).padStart(2,'0')).join('');}
export function computeOutcomeIndicators(s,d){
  const m={...s.starting_meters}; const change=(k,v)=>{m[k]=Math.max(0,Math.min(100,Number(m[k]||0)+Number(v||0)));};
  if(s.correct_confidence_range.includes(d.confidence)){change('truth_integrity',10);change('institutional_credibility',6);} else if(s.unsafe_choices.includes(d.confidence)){change('truth_integrity',-25);change('escalation_risk',18);change('institutional_credibility',-18);} else change('truth_integrity',-5);
  if(s.correct_corroboration_range.includes(d.corroboration))change('truth_integrity',6);else if(s.unsafe_corroboration_choices.includes(d.corroboration)){change('truth_integrity',-12);change('escalation_risk',8);}
  if(s.correct_authenticity_range.includes(d.authenticity))change('truth_integrity',6);else if(s.unsafe_authenticity_choices.includes(d.authenticity)){change('truth_integrity',-12);change('institutional_credibility',-8);}
  const rel=s.release_options.find(o=>o.id===d.release_id);for(const [k,v] of Object.entries(rel?.effects||{}))change(k,v);
  if(d.actions.protect_civilians){change('civilian_safety',20);change('institutional_credibility',5);}else{change('civilian_safety',-18);change('institutional_credibility',-5);}
  if(d.actions.info_integrity_review){change('truth_integrity',10);change('escalation_risk',-10);change('public_pressure',-4);}else change('truth_integrity',-6);
  if(d.actions.deescalation_channel){change('escalation_risk',-14);change('institutional_credibility',4);} if(d.actions.request_original_media){change('truth_integrity',8);change('institutional_credibility',3);} if(d.actions.senior_review)change('institutional_credibility',9); if(d.actions.humanitarian_check){change('civilian_safety',10);change('institutional_credibility',4);}
  const elapsed=Math.max(0,Number(s.decision_clock_minutes||30)-Number(d.remaining_minutes||0));m.decision_timeliness=Math.max(0,m.decision_timeliness-Math.ceil(elapsed/2));return {evidence_integrity:m.truth_integrity,escalation_control:100-m.escalation_risk,civilian_protection:m.civilian_safety,institutional_credibility:m.institutional_credibility,decision_timeliness:m.decision_timeliness,public_pressure:m.public_pressure};
}
