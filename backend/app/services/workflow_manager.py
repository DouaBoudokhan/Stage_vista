"""Stock Entry Workflow Manager"""
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..schemas.stock_entry import WorkflowState, PurchaseOrderInfo


class WorkflowManager:
    """Manages Stock Entry workflow state across multiple steps"""
    
    def __init__(self):
        # In-memory storage for workflow states
        # In production, this should be stored in Redis or database
        self._workflows: Dict[str, WorkflowState] = {}
        self._cleanup_interval = timedelta(hours=2)  # Auto-cleanup after 2 hours
    
    def create_workflow(self) -> str:
        """
        Create a new workflow session
        
        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            step=1,
            created_at=datetime.utcnow()
        )
        
        self._workflows[workflow_id] = workflow_state
        return workflow_id
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow state by ID"""
        self._cleanup_expired_workflows()
        return self._workflows.get(workflow_id)
    
    def update_workflow_step1(
        self, 
        workflow_id: str, 
        category: str, 
        confidence: float
    ) -> bool:
        """Update workflow after Step 1 (Product Detection)"""
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow.step != 1:
            return False
        
        workflow.category = category
        workflow.confidence = confidence
        workflow.step = 2
        
        return True
    
    def update_workflow_step2(
        self,
        workflow_id: str,
        supplier: str,
        document_number: str,
        purchase_orders: list,
        extracted_text: str
    ) -> bool:
        """Update workflow after Step 2 (Document OCR)"""
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow.step != 2:
            return False
        
        # Convert dicts to PurchaseOrderInfo objects if needed
        po_list = []
        for po in purchase_orders:
            if isinstance(po, dict):
                po_list.append(PurchaseOrderInfo(**po))
            else:
                po_list.append(po)
        
        workflow.supplier = supplier
        workflow.document_number = document_number
        workflow.purchase_orders = po_list
        workflow.extracted_texts["document"] = extracted_text
        workflow.step = 3
        
        return True
    
    def update_workflow_step3(
        self,
        workflow_id: str,
        selected_po_number: str
    ) -> bool:
        """Update workflow after Step 3 (PO Selection)"""
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow.step != 3:
            return False
        
        # Find selected PO in available options
        selected_po = None
        for po in workflow.purchase_orders:
            if po.po_number == selected_po_number:
                selected_po = po
                break
        
        if not selected_po:
            return False
        
        workflow.selected_po = selected_po
        workflow.serial_numbers = selected_po.serial_numbers.copy()
        workflow.step = 4
        
        return True
    
    def update_workflow_step4(
        self,
        workflow_id: str,
        brand: str,
        product_name: str,
        article_number: str,
        quantity: int,
        po_on_package: Optional[str],
        extracted_text: str
    ) -> bool:
        """Update workflow after Step 4 (Package Label)"""
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow.step != 4:
            return False
        
        workflow.brand = brand
        workflow.product_name = product_name
        workflow.article_number = article_number
        workflow.quantity = quantity
        workflow.po_on_package = po_on_package
        workflow.extracted_texts["package"] = extracted_text
        
        # Check for PO mismatch warning
        if po_on_package and workflow.selected_po and po_on_package != workflow.selected_po.po_number:
            warning = f"PO mismatch: Selected {workflow.selected_po.po_number}, Package shows {po_on_package}"
            workflow.warnings.append(warning)
        
        workflow.step = 5
        
        return True
    
    def complete_workflow(self, workflow_id: str) -> bool:
        """Mark workflow as completed"""
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow.step != 5:
            return False
        
        workflow.step = 6  # Completed
        return True
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow session"""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow status and next action"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return {
                "exists": False,
                "message": "Workflow not found or expired"
            }
        
        step_info = {
            1: {"name": "Product Detection", "next_action": "scan_product"},
            2: {"name": "Document OCR", "next_action": "scan_document"},
            3: {"name": "PO Selection", "next_action": "select_purchase_order"},
            4: {"name": "Package Label", "next_action": "scan_package"},
            5: {"name": "Save Entry", "next_action": "save_stock_entry"},
            6: {"name": "Completed", "next_action": None}
        }
        
        current_step_info = step_info.get(workflow.step, {"name": "Unknown", "next_action": None})
        
        return {
            "exists": True,
            "workflow_id": workflow_id,
            "current_step": workflow.step,
            "step_name": current_step_info["name"],
            "next_action": current_step_info["next_action"],
            "status": "COMPLETED" if workflow.step == 6 else "IN_PROGRESS",
            "warnings": workflow.warnings,
            "created_at": workflow.created_at.isoformat()
        }
    
    def _cleanup_expired_workflows(self):
        """Remove expired workflow sessions"""
        current_time = datetime.utcnow()
        expired_ids = []
        
        for workflow_id, workflow in self._workflows.items():
            if current_time - workflow.created_at > self._cleanup_interval:
                expired_ids.append(workflow_id)
        
        for workflow_id in expired_ids:
            del self._workflows[workflow_id]
    
    def list_active_workflows(self) -> Dict[str, Any]:
        """List all active workflows (for debugging)"""
        self._cleanup_expired_workflows()
        
        return {
            "active_count": len(self._workflows),
            "workflows": [
                {
                    "workflow_id": wf.workflow_id,
                    "step": wf.step,
                    "created_at": wf.created_at.isoformat(),
                    "category": wf.category,
                    "supplier": wf.supplier
                }
                for wf in self._workflows.values()
            ]
        }


# Global instance
workflow_manager = WorkflowManager()