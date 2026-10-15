function toggleSidebar(){document.getElementById('sidebar')?.classList.toggle('open')}
function togglePassword(inputId='password',buttonId='password-toggle'){const input=document.getElementById(inputId);if(!input)return;const show=input.type==='password';input.type=show?'text':'password';const button=document.getElementById(buttonId);if(button){button.innerHTML=show?'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3l18 18M10.6 10.6a2 2 0 002.8 2.8"></path><path d="M9.9 5.2A10.8 10.8 0 0112 5c6.4 0 10 7 10 7a15.4 15.4 0 01-3.1 3.9M6.2 6.2C3.5 8 2 12 2 12s3.6 7 10 7a10.7 10.7 0 004.1-.8"></path></svg>':'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"></path><circle cx="12" cy="12" r="3"></circle></svg>';button.setAttribute('aria-label',show?'Hide password':'Show password');button.setAttribute('title',show?'Hide password':'Show password')}}
function toast(message){const old=document.querySelector('.toast');if(old)old.remove();const el=document.createElement('div');el.className='toast';el.textContent=message;document.body.appendChild(el);setTimeout(()=>el.remove(),2800)}
let activeTicketStatus='all';
function filterRows(status){activeTicketStatus=status;applyTicketFilters()}
function searchTickets(){applyTicketFilters()}
function applyTicketFilters(){const table=document.getElementById('ticketTable');if(!table)return;const query=(document.getElementById('ticketSearch')?.value||'').trim().toLowerCase();const rows=table.querySelectorAll('tbody tr[data-status]');let visible=0;rows.forEach(row=>{const statusMatch=activeTicketStatus==='all'||(activeTicketStatus==='completed'?['resolved','closed'].includes(row.dataset.status):row.dataset.status===activeTicketStatus);const searchMatch=!query||(row.dataset.search||'').toLowerCase().includes(query);row.hidden=!(statusMatch&&searchMatch);if(!row.hidden)visible++});const empty=table.querySelector('#ticketSearchEmpty');if(empty)empty.hidden=rows.length===0||visible>0}
document.addEventListener('DOMContentLoaded',()=>{
	document.querySelectorAll('.alert').forEach(a=>setTimeout(()=>a.remove(),4500));
});

document.addEventListener('DOMContentLoaded',()=>{
	const category=document.getElementById('id_category');
	const issue=document.getElementById('id_issue_type');
	const otherIssue=document.getElementById('id_other_issue');
	const choiceWrap=document.querySelector('[data-issue-choice]');
	const otherWrap=document.querySelector('[data-issue-other]');
	if(!category||!issue||!otherIssue||!choiceWrap||!otherWrap)return;
	const issueMap=JSON.parse(category.dataset.issueMap||'{}');
	const customIssueOption='Other / Type your own issue';

	function updateIssueField(preserveSelection){
		const selectedIssue=preserveSelection?issue.value:'';
		const options=issueMap[category.value]||[];
		const isOther=category.options[category.selectedIndex]?.textContent.trim()==='Other';
		issue.replaceChildren(new Option('Select a specific issue',''));
		options.forEach(issueName=>issue.add(new Option(issueName,issueName)));
		if(options.includes(selectedIssue)){
			issue.value=selectedIssue;
		}else if(options.length && !preserveSelection){
			issue.value='';
		}
		const needsCustomText=isOther && issue.value===customIssueOption;
		if(!needsCustomText)otherIssue.value='';
		choiceWrap.hidden=!category.value;
		otherWrap.hidden=!needsCustomText;
		issue.disabled=!category.value;
		issue.required=!!category.value;
		otherIssue.required=needsCustomText;
	}

	category.addEventListener('change',()=>updateIssueField(false));
	issue.addEventListener('change',()=>updateIssueField(true));
	updateIssueField(true);
});

document.addEventListener('DOMContentLoaded',()=>{
	const filters=document.getElementById('ticketFilters');
	if(!filters)return;
	filters.querySelectorAll('select').forEach(select=>{
		select.addEventListener('change',()=>filters.requestSubmit());
	});
});

document.addEventListener('DOMContentLoaded',()=>{
	const dialog=document.getElementById('guideDialog');
	if(!dialog)return;

	const slides=[...dialog.querySelectorAll('.guide-slide')];
	const title=document.getElementById('guideTitle');
	const progress=document.getElementById('guideProgress');
	const previous=document.getElementById('guidePrevious');
	const next=document.getElementById('guideNext');
	const close=document.getElementById('guideClose');
	let activeSlide=0;

	function showSlide(index){
		activeSlide=Math.max(0,Math.min(index,slides.length-1));
		slides.forEach((slide,slideIndex)=>{slide.hidden=slideIndex!==activeSlide});
		title.textContent=slides[activeSlide].dataset.title;
		progress.textContent=`Example ${activeSlide+1} of ${slides.length}`;
		previous.disabled=activeSlide===0;
		next.disabled=activeSlide===slides.length-1;
	}

	document.querySelectorAll('.article-trigger').forEach((trigger)=>{
		trigger.addEventListener('click',()=>{
			showSlide(Number(trigger.dataset.slideIndex));
			dialog.showModal();
		});
	});

	previous.addEventListener('click',()=>showSlide(activeSlide-1));
	next.addEventListener('click',()=>showSlide(activeSlide+1));
	close.addEventListener('click',()=>dialog.close());
	dialog.addEventListener('click',(event)=>{
		if(event.target===dialog)dialog.close();
	});
	dialog.addEventListener('keydown',(event)=>{
		if(event.key==='ArrowLeft'&&!previous.disabled)showSlide(activeSlide-1);
		if(event.key==='ArrowRight'&&!next.disabled)showSlide(activeSlide+1);
	});
});

document.addEventListener('DOMContentLoaded',()=>{
	const toggle=document.getElementById('notificationToggle');
	const panel=document.getElementById('notificationPanel');
	const wrap=document.getElementById('notificationWrap');
	if(!toggle||!panel||!wrap)return;
	const list=document.getElementById('notificationList');
	const countBadge=document.getElementById('notificationCount');
	const dot=document.getElementById('notificationDot');
	const unreadLabel=document.getElementById('notificationUnreadLabel');
	const markAllForm=document.getElementById('notificationMarkAll');
	let refreshing=false;

	function setOpen(open){
		panel.hidden=!open;
		toggle.setAttribute('aria-expanded',String(open));
	}

	function renderNotifications(notifications){
		list.replaceChildren();
		if(!notifications.length){
			const empty=document.createElement('p');
			empty.className='notification-empty';
			empty.textContent='No notifications yet. Ticket activity will appear here.';
			list.append(empty);
			return;
		}

		notifications.forEach(notification=>{
			const row=document.createElement('a');
			row.className=`notification-row${notification.unread?' unread':''}`;
			row.href=notification.url;
			const heading=document.createElement('strong');
			heading.textContent=notification.message;
			const ticketDetails=document.createElement('span');
			ticketDetails.textContent=`${notification.submitter} submitted: "${notification.ticket_title}"`;
			const timestamp=document.createElement('span');
			timestamp.textContent=`${notification.ticket_number} · ${notification.created_at}`;
			row.append(heading,ticketDetails,timestamp);
			list.append(row);
		});
	}

	async function refreshNotifications(){
		if(refreshing)return;
		refreshing=true;
		try{
			const response=await fetch(wrap.dataset.feedUrl,{headers:{'Accept':'application/json'},credentials:'same-origin',cache:'no-store'});
			if(!response.ok)return;
			const data=await response.json();
			const unreadCount=Number(data.unread_count)||0;
			countBadge.textContent=String(unreadCount);
			countBadge.hidden=unreadCount===0;
			dot.hidden=unreadCount===0;
			unreadLabel.textContent=`${unreadCount} unread`;
			unreadLabel.hidden=unreadCount===0;
			markAllForm.hidden=unreadCount===0;
			toggle.setAttribute('aria-label',unreadCount?`Notifications, ${unreadCount} unread`:'Notifications');
			renderNotifications(data.notifications||[]);
		}catch(error){
			console.error('Unable to refresh notifications.',error);
		}finally{
			refreshing=false;
		}
	}

	toggle.addEventListener('click',()=>setOpen(panel.hidden));
	document.addEventListener('click',(event)=>{
		if(!wrap.contains(event.target))setOpen(false);
	});
	document.addEventListener('keydown',(event)=>{
		if(event.key==='Escape')setOpen(false);
	});
	markAllForm.addEventListener('submit',async event=>{
		event.preventDefault();
		try{
			const response=await fetch(markAllForm.action,{
				method:'POST',
				body:new FormData(markAllForm),
				headers:{'X-Requested-With':'XMLHttpRequest','Accept':'application/json'},
				credentials:'same-origin',
			});
			if(!response.ok)throw new Error(`Notification update failed: ${response.status}`);
			await refreshNotifications();
		}catch(error){
			console.error('Unable to mark notifications as read.',error);
			markAllForm.submit();
		}
	});
	refreshNotifications();
	window.setInterval(refreshNotifications,5000);
	document.addEventListener('visibilitychange',()=>{
		if(document.visibilityState==='visible')refreshNotifications();
	});
});
