from flask import Blueprint, jsonify, send_file, request
import os
import uuid
from super_admin_1.models.alternative import Database
from super_admin_1 import db
from super_admin_1.models.shop import Shop
from super_admin_1.models.shop_logs import ShopsLogs
from super_admin_1.models.product import Product
from super_admin_1.models.user import User
from super_admin_1.shop.shoplog_helpers import ShopLogs
from sqlalchemy.exc import SQLAlchemyError
from super_admin_1.shop.shop_schemas import IdSchema
from pydantic import ValidationError
from utils import raise_validation_error
from sqlalchemy import func


shop = Blueprint("shop", __name__, url_prefix="/api/shop")


# TEST
@shop.route("/endpoint", methods=["GET"])
# @admin_required(request=request)
def shop_endpoint():
    """
    Handle GET requests to the shop endpoint.

    Returns:
        jsonify: A JSON response indicating the success of the request.
    """
    response_data = {
        "message": "This is the shop endpoint under /api/shop/endpoint"}
    return jsonify(response_data), 200


@shop.route("/all", methods=["GET"])
# @admin_required(request=request)
def get_shops():
    """get information to all shops

     Returns:
        dict: A JSON response with the appropriate status code and message.
            - If the shops are returned successfully:
                - Status code: 200
                - Body:
                    - "message": "all shops request successful"
                    - "data": []
                    - "total_shops": 0
                    - "total_deleted_shops": 0
                    - "total_banned_shops": 0
            - If an exception occurs during the get process:
                - Status code: 500
                - Body:
                    - "error": "Internal Server Error"
                    - "message": [error message]
    """

    shops = Shop.query.all()
    data = []

    def check_status(shop):
        if shop.admin_status == "suspended" and shop.restricted == "temporary":
            return "Banned"
        if (shop.admin_status == "approved" or shop.admin_status == "pending") and shop.is_deleted == "active":
            return "Active"
        if shop.is_deleted == "temporary":
            return "Deleted"

    total_shops = Shop.query.count()
    banned_shops = Shop.query.filter_by(
        admin_status='suspended', restricted='temporary').count()
    deleted_shops = Shop.query.filter_by(is_deleted="temporary").count()

    try:
        for shop in shops:
            products = Product.query.filter_by(shop_id=shop.id).all()
            merchant_name = f"{shop.user.first_name} {shop.user.last_name}"
            joined_date = shop.createdAt.strftime("%d-%m-%Y")
            shop_data = {
                "vendor_id": shop.id,
                "vendor_name": shop.name,
                "merchant_id": shop.merchant_id,
                "merchant_name": merchant_name,
                "merchant_email": shop.user.email,
                "policy_confirmation": shop.policy_confirmation,
                "restricted": shop.restricted,
                "admin_status": shop.admin_status,
                "is_deleted": shop.is_deleted,
                "reviewed": shop.reviewed,
                "rating": shop.rating,
                "createdAt": shop.createdAt,
                "joined_date": joined_date,
                "updatedAt": shop.updatedAt,
                "vendor_status": check_status(shop),
                "total_products": len(products)
            }
            data.append(shop_data)
        return jsonify({"message": "all shops information", "data": data, "total_shops": total_shops,
                        "total_banned_shops": banned_shops, "total_deleted_shops": deleted_shops})
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

# WORKS


@shop.route("/specific/<shop_id>", methods=["GET"])
# @admin_required(request=request)
def get_specific_shop(shop_id):
    """get information to a shop

    Returns:
        dict: A JSON response with the appropriate status code and message.
            - If the shop is returned successfully:
                - Status code: 200
                - Body:
                    - "message": "the shop information"
                    - "data": []
            - If the shop with the given ID does not exist:
                - Status code: 404
                - Body:
                    - "error": "not found"
                    - "message": "invalid shop id"
            - If an exception occurs during the get process:
                - Status code: 500
                - Body:
                    - "error": "Internal Server Error"
                    - "message": [error message]
    """
    try:
        shop_id = IdSchema(id=shop_id)
        shop_id = shop_id.id
    except ValidationError as e:
        raise_validation_error(e)
    shop = Shop.query.filter_by(id=shop_id).first()
    data = []

    if not shop:
        return jsonify({"error": "not found", "message": "invalid shop id"}), 404

    def check_status(shop):
        if shop.admin_status == "suspended" and shop.restricted == "temporary":
            return "Banned"
        if (shop.admin_status == "approved" or shop.admin_status == "pending") and shop.is_deleted == "active":
            return "Active"
        if shop.is_deleted == "temporary":
            return "Deleted"

    def check_product_status(product):
        if product.admin_status == "suspended" and product.is_deleted == "temporary":
            return "Sanctioned"
        if (product.admin_status == "approved" or product.admin_status == "pending") and product.is_deleted == "active":
            return "Active"
        if product.is_deleted == "temporary":
            return "Deleted"

    try:
        products = Product.query.filter_by(shop_id=shop.id).all()
        total_products = Product.query.filter_by(shop_id=shop.id).count()
        merchant_name = f"{shop.user.first_name} {shop.user.last_name}"
        joined_date = shop.createdAt.strftime("%d-%m-%Y")
        shop_data = {
            "vendor_id": shop.id,
            "vendor_name": shop.name,
            "merchant_id": shop.merchant_id,
            "merchant_name": merchant_name,
            "merchant_email": shop.user.email,
            "policy_confirmation": shop.policy_confirmation,
            "restricted": shop.restricted,
            "admin_status": shop.admin_status,
            "is_deleted": shop.is_deleted,
            "reviewed": shop.reviewed,
            "rating": shop.rating,
            "createdAt": shop.createdAt,
            "joined_date": joined_date,
            "updatedAt": shop.updatedAt,
            "vendor_status": check_status(shop),
            "total_products": total_products,
            "products": [{
                "product_id": product.id,
                # "product_rating_id": product.rating_id,
                "category_id": product.category_id,
                "product_name": product.name,
                "description": product.description,
                "quantity": product.quantity,
                "price": product.price,
                "discount_price": product.discount_price,
                "tax": product.tax,
                "product_admin_status": product.admin_status,
                "product_is_deleted": product.is_deleted,
                "product_is_published": product.is_published,
                "currency": product.currency,
                "createdAt": product.createdAt,
                "updatedAt": product.updatedAt,
                "product_status": check_product_status(product),
                "product_date_added": product.createdAt.strftime("%d-%m-%Y")
            } for product in products]
        }
        #  "image_id": product.image_id, "rating_id": product.rating_id
        data.append(shop_data)
        return jsonify({"message": "the shop information", "data": data}), 200
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


@shop.route("/ban_vendor/<vendor_id>", methods=["PUT"])
# @admin_required(request=request)
def ban_vendor(vendor_id):
    """
    Handle PUT requests to ban a vendor by updating their shop data.

    Args:
        vendor_id (uuid): The unique identifier of the vendor to be banned.

    Returns:
        jsonify: A JSON response containing the status of the vendor banning operation.
    """
    try:
        # Check if the vendor is already banned
        check_query = """
            SELECT "restricted" FROM "shop"
            WHERE "id" = %s
        """
        vendor_id = IdSchema(id=vendor_id)
        vendor_id = vendor_id.id
        with Database() as cursor:
            cursor.execute(check_query, (vendor_id,))
            current_state = cursor.fetchone()

        if current_state and current_state[0] == "temporary":
            return (
                jsonify(
                    {
                        "error": "Conflict",
                        "message": "Action already carried out on this Shop",
                    }
                ),
                409,
            )

        # Extract the reason from the request payload
        data = request.get_json()
        reason = data.get("reason")

        if not reason:
            return (
                jsonify(
                    {
                        "error": "Bad Request",
                        "message": "Supply the reason for banning this vendor.",
                    }
                ),
                400,
            )

        # Proceed with banning the vendor
        update_query = """
            UPDATE "shop"
            SET "restricted" = 'temporary', 
                "admin_status" = 'suspended'
            WHERE "id" = %s
            RETURNING *;  -- Return the updated row
        """
        with Database() as cursor:
            cursor.execute(update_query, (vendor_id,))
            updated_vendor = cursor.fetchone()

        if updated_vendor:
            vendor_details = {
                "id": updated_vendor[0],
                "merchant_id": updated_vendor[1],
                "name": updated_vendor[2],
                "policy_confirmation": updated_vendor[3],
                "restricted": updated_vendor[4],
                "admin_status": updated_vendor[5],
                "is_deleted": updated_vendor[6],
                "reviewed": updated_vendor[7],
                "rating": float(updated_vendor[8]),
                "created_at": str(updated_vendor[9]),
                "updated_at": str(updated_vendor[10]),
            }
            return jsonify({
                "message": "Vendor account banned temporarily.",
                "vendor_details": vendor_details,
                "reason": reason,
                "data": vendor_details
            }), 201

        else:
            return jsonify({"error": "Vendor not found."}), 404
    except ValidationError as e:
        raise_validation_error(e)
    except Exception as e:
        print(str(e))
        return jsonify({"error": "Internal Server Error"}), 500

# WORKS


@shop.route("/banned_vendors", methods=["GET"])
# @admin_required(request=request)
def get_banned_vendors():

    try:
        # Perform a database query to retrieve all banned vendors
        query = """
            SELECT * FROM "shop"
            WHERE "restricted" = 'temporary' AND "admin_status" = 'suspended'
        """

        with Database() as cursor:
            cursor.execute(query)
            banned_vendors = cursor.fetchall()

        # Prepare the response data
        banned_vendors_list = []
        for vendor in banned_vendors:
            vendor_details = {
                "id": vendor[0],
                "merchant_id": vendor[1],
                "name": vendor[2],
                "policy_confirmation": vendor[3],
                "restricted": vendor[4],
                "admin_status": vendor[5],
                "is_deleted": vendor[6],
                "reviewed": vendor[7],
                "rating": float(vendor[8]),
                "created_at": str(vendor[9]),
                "updated_at": str(vendor[10]),
            }
            banned_vendors_list.append(vendor_details)

        # Return the list of banned vendors in the response
        return jsonify({
            "message": "Banned vendors retrieved successfully.",
            "data": banned_vendors_list
        }), 200

    except Exception as e:
        print(str(e))
        return jsonify({"error": "Internal Server Error"}), 500


# Define a route to unban a vendor
# WORKS
@shop.route("/unban_vendor/<vendor_id>", methods=["PUT"])
# @admin_required(request=request)
def unban_vendor(vendor_id):
    """
    Unban a vendor by setting their 'restricted' and 'admin_status' fields.

    Args:
        vendor_id (string): The unique identifier of the vendor to unban.

    Returns:
        JSON response with status and message:
        - Success (HTTP 200): Vendor unbanned successfully.
        - Error (HTTP 404): If the vendor with the provided ID is not found.
        - Error (HTTP 500): If an error occurs during the database operation.

    Note:
    - This endpoint is used to unban a vendor by updating their 'restricted' and 'admin_status' fields.
    - The 'restricted' field is set to 'no' to indicate that the vendor is no longer restricted.
    - The 'admin_status' field is set to 'approved' to indicate that the vendor's status has been updated.
    - Proper authentication and authorization checks should be added to secure this endpoint.
    """
    try:
        try:
            vendor_id = IdSchema(id=vendor_id)
            vendor_id = vendor_id.id
        except ValidationError as e:
            raise_validation_error(e)

        # Search the database for the vendor with the provided vendor_id
        vendor = Shop.query.filter_by(id=vendor_id).first()
        # If the vendor with the provided ID doesn't exist, return a 404 error
        if not vendor:
            return jsonify({"Error": "Not Found", "message": "Vendor not found."}), 404

        # Check if the shop associated with the vendor is active
        # if vendor.is_deleted != "active":
        #    return jsonify(
        #            {
        #                "Error": "Bad Request",
        #                "message": "Vendor's shop is not active. Cannot unban.",
        #            }
        #        ), 400

        # Check if the vendor is already unbanned
        if vendor.restricted == "no":
            return (
                jsonify(
                    {"status": "Error", "message": "Vendor is already unbanned."}),
                400,
            )

            return (
                jsonify(
                    {"Error": "Conflict", "message": "Vendor is already unbanned."}
                ),
                409,
            )

        # Unban the vendor by setting 'restricted' to 'no' and
        # updating 'admin_status' to 'approved'
        vendor.restricted = "no"
        vendor.admin_status = "approved"

        # Commit the changes to the database
        db.session.commit()

        # Construct vendor details for the response
        vendor_details = {
            "id": vendor.id,
            "merchant_id": vendor.merchant_id,
            "name": vendor.name,
            "policy_confirmation": vendor.policy_confirmation,
            "restricted": vendor.restricted,
            "admin_status": vendor.admin_status,
            "is_deleted": vendor.is_deleted,
            "reviewed": vendor.reviewed,
            "rating": float(vendor.rating),
            "created_at": str(vendor.created_at),
            "updated_at": str(vendor.updated_at),
        }

        # Return a success message
        return (
            jsonify(
                {
                    "message": "Vendor unbanned successfully.",
                    "vendor_details": vendor_details,
                }
            ),
            200,
        )
    except SQLAlchemyError as e:
        # If an error occurs during the database operation, roll back the transaction
        db.session.rollback()
        return jsonify({"status": "Error.", "message": str(e)}), 500


@shop.route("restore_shop/<shop_id>", methods=["PATCH"])
# @admin_required(request=request)
def restore_shop(shop_id):
    """restores a deleted shop by setting their "temporary" to "active" fields
    Args:
        shop_id (string)
    returns:
        JSON response with status code and message:
        -success(HTTP 200):shop restored successfully
        -success(HTTP 200): if the shop with provided not marked as deleted
    """
    try:
        shop_id = IdSchema(id=shop_id)
        shop_id = shop_id.id
    except ValidationError as e:
        raise_validation_error(e)
    try:
        shop = Shop.query.filter_by(id=shop_id).first()
    except Exception as e:
        if not shop:
            return jsonify({"Error": "Not Found", "Message": "Shop Not Found"}), 404

    # change the object attribute from temporary to active
    if shop.is_deleted == "temporary":
        shop.is_deleted = "active"
        try:
            db.session.commit()

            """
            The following logs the action in the shop_log db
            """
            get_user_id = shop.user.id
            action = ShopLogs(shop_id=shop_id, user_id=get_user_id)
            action.log_shop_deleted(delete_type="active")

            return (
                jsonify(
                    {"message": "shop restored successfully", "data": shop.format()}
                ),
                201,
            )
        except Exception as e:
            return jsonify(
                {
                    "Error": "Internal Server Error",
                    "message": str(e),
                }
            )
    else:
        return (
            jsonify(
                {
                    "error": "Conflict",
                    "message": "Action already carried out on this Shop",
                }
            ),
            409,
        )


@shop.route("delete_shop/<shop_id>", methods=["PATCH"], strict_slashes=False)
# @admin_required(request=request)
def delete_shop(shop_id):
    """Delete a shop and cascade temporary delete action"""
    try:
        shop_id = IdSchema(id=shop_id)
        shop_id = shop_id.id
    except ValidationError as e:
        raise_validation_error(e)
    # verify if shop exists
    try:
        shop = Shop.query.filter_by(id=shop_id).first()
    except Exception as e:
        if not shop:
            return jsonify({"error": "Not Found", "message": "Shop not found"}), 404
    # check if shop is temporary
    if shop.is_deleted == "temporary":
        return (
            jsonify(
                {
                    "error": "Conflict",
                    "message": "Action already carried out on this Shop",
                }
            ),
            409,
        )
    data = request.get_json()
    reason = data.get("reason")

    if not reason:
        return (
            jsonify({"error": "Supply a reason for temporarily deleting this shop"}),
            400,
        )

        return (
            jsonify(
                {
                    "error": "Bad Request",
                    "message": "Supply a reason for temporarily deleting this shop",
                }
            ),
            400,
        )

    # delete shop temporarily
    shop.is_deleted = "temporary"
    # Cascade the temporary delete action to associated products
    products = Product.query.filter_by(shop_id=shop_id).all()
    for product in products:
        product.is_deleted = 'temporary'
        db.session.add(product)

    db.session.commit()

    """
    The following logs the action in the shop_log db
    """
    get_user_id = shop.user.id
    action = ShopLogs(shop_id=shop_id, user_id=get_user_id)
    action.log_shop_deleted(delete_type="temporary")

    return jsonify({'message': "Shop and associated products temporarily deleted", "reason": reason}), 204


# delete shop object permanently out of the DB

@shop.route("delete_shop/<shop_id>", methods=["DELETE"])
# @admin_required(request=request)
def perm_del(shop_id):
    """Delete a shop"""
    try:
        shop_id = IdSchema(id=shop_id)
        shop_id = shop_id.id
    except ValidationError as e:
        raise_validation_error(e)

    """ Delete a shop permanently also while shop is deleted all the 
    product associated with it will also be deleted permanently from the shop"""
    try:
        shop = Shop.query.filter_by(id=shop_id).first()
        if not shop:
            return jsonify({'message': 'Shop not found'}), 400
        # access associated products
        products = Product.query.filter_by(shop_id=shop_id).all()
        # access reviews for each product and delete them one by one
        for product in products:
            db.session.delete(product)
            db.session.commit()

        db.session.delete(shop)
        db.session.commit()
        return jsonify({'message': 'Shop and associated products deleted permanently'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

# Define a route to get all temporarily deleted vendors


@shop.route("/temporarily_deleted_vendors", methods=["GET"], strict_slashes=False)
# @admin_required(request=request)
def get_temporarily_deleted_vendors():
    """
    Retrieve temporarily deleted vendors.

    This endpoint allows super admin users to retrieve a list of vendors who have been temporarily deleted.

    Returns:
        JSON response with status and message:
        - Success (HTTP 200): A list of temporarily deleted vendors and their details.
        - Success (HTTP 200): A message indicating that no vendors have been temporarily deleted.
        - Error (HTTP 500): If an error occurs during the retrieving process.

    Permissions:
        - Only accessible to super admin users.

    Note:
        - The list includes the details of vendors who have been temporarily deleted.
        - If no vendors have been temporarily deleted, a success message is returned.
    """
    try:
        # Query the database for all temporarily_deleted_vendors
        temporarily_deleted_vendors = Shop.query.filter_by(
            is_deleted="temporary").all()

        # Calculate the total count of temporarily deleted vendors
        total_count = len(temporarily_deleted_vendors)

        # Check if no vendors have been temporarily deleted
        if not temporarily_deleted_vendors:
            return (
                jsonify(
                    {
                        "status": "Success",
                        "message": "No vendors have been temporarily deleted",
                        "count": total_count,
                    }
                ),
                200,
            )

        # Create a list with vendors details
        vendors_list = [vendor.format()
                        for vendor in temporarily_deleted_vendors]

        # Return the list with all attributes of the temporarily_deleted_vendors
        return (
            jsonify(
                {
                    "status": "Success",
                    "message": "All temporarily deleted vendors retrieved successfully",
                    "temporarily_deleted_vendors": vendors_list,
                    "count": total_count,
                }
            ),
            200,
        )

    except Exception as e:
        # Handle any exceptions that may occur during the retrieving process
        return jsonify({"status": "Error", "message": str(e)})


# Define a route to get details of a temporarily deleted vendor based on his/her ID
@shop.route(
    "/temporarily_deleted_vendor/<string:vendor_id>",
    methods=["GET"],
    strict_slashes=False,
)
# @admin_required(request=request)
def get_temporarily_deleted_vendor(vendor_id):
    """
    Retrieve details of a temporarily deleted vendor based on its ID.

    Args:
        vendor_id (string): The unique identifier of the vendor to retrieve.

    Returns:
        JSON response with status and message:
        - Success (HTTP 200): Details of the temporarily deleted vendor.
        - Error (HTTP 404): If the vendor with the provided ID is not found or not temporarily deleted.
        - Error (HTTP 500): If an error occurs during the retrieval process.

    Permissions:
        - Only accessible to super admin users.

    Note:
        - This endpoint allows super admin users to retrieve the details of a temporarily deleted vendor based on his/her ID.
    """
    try:
        try:
            vendor_id = IdSchema(id=vendor_id)
            vendor_id = vendor_id.id
        except ValidationError as e:
            raise_validation_error(e)

        # Query the database for the vendor with the provided vendor_id that is temporarily deleted
        temporarily_deleted_vendor = Shop.query.filter_by(
            id=vendor_id, is_deleted="temporary"
        ).first()

        # If the vendor with the provided ID doesn't exist or is not temporarily deleted, return a 404 error
        if not temporarily_deleted_vendor:
            return (
                jsonify(
                    {
                        "status": "Error",
                        "message": "Temporarily deleted vendor not found.",
                    }
                ),
                404,
            )

        # Return the details of the temporarily deleted vendor
        vendor_details = temporarily_deleted_vendor.format()

        return (
            jsonify(
                {
                    "status": "Success",
                    "message": "Temporarily deleted vendor details retrieved successfully",
                    "temporarily_deleted_vendor": vendor_details,
                }
            ),
            200,
        )

    except SQLAlchemyError as e:
        # Handle any exceptions that may occur during the retrieval process
        db.session.rollback()
        return jsonify({"status": "Error", "message": str(e)}), 500


logs = Blueprint("logs", __name__, url_prefix="/api/logs")


@logs.route("/shops", defaults={"shop_id": None})
@logs.route("/shops/<shop_id>")
# @admin_required(request=request)
def get_all_shop_logs(shop_id):
    """Get all shop logs"""
    if not shop_id:
        return (
            jsonify(
                {
                    "message": "success",
                    "logs": [
                        log.format() if log else [] for log in ShopsLogs.query.all()
                    ],
                }
            ),
            200,
        )

    return (
        jsonify(
            {
                "message": "success",
                "logs": [
                    log.format() if log else []
                    for log in ShopsLogs.query.filter_by(shop_id=shop_id).all()
                ],
            }
        ),
        200,
    )


@logs.route("/shops/download", defaults={"shop_id": None})
@logs.route("/shops/<shop_id>/download")
# @admin_required(request=request)
def download_shop_logs(shop_id):
    """Download all shop logs"""
    logs = []
    if not shop_id:
        logs = [log.format() if log else [] for log in ShopsLogs.query.all()]
    else:
        logs = [
            log.format() if log else []
            for log in ShopsLogs.query.filter_by(shop_id=shop_id).all()
        ]
    # Create a temporary file to store the strings
    temp_file_path = f"{os.path.abspath('.')}/temp_file.txt"
    with open(temp_file_path, "w") as temp_file:
        temp_file.write("\n".join(logs))

    response = send_file(
        temp_file_path, as_attachment=True, download_name="shoplogs.txt"
    )
    os.remove(temp_file_path)

    return response


@logs.route("/shop/actions", methods=["GET"])
# @admin_required(request=request)
def shop_actions():
    data = ShopsLogs.query.all()
    return jsonify([action.format_json() for action in data]), 200


@shop.route("/sanctioned", methods=["GET"])
# # @admin_required(request=request)
def sanctioned_shop():
    """
    Get all sanctioned products from the database.

    Args:
      None

    Returns:
      A JSON response containing a message and a list of dictionary objects representing the sanctioned shop.
      If no shop are found, the message will indicate that and the object will be set to None.
    """
    data = []
    # get all the product object, filter by is_delete = temporay and rue and admin_status = "suspended"
    query = Shop.query.filter(
        Shop.admin_status == "suspended",
    )

    # if the query is empty
    if not query.all():

        return jsonify({"message": "No shops found", "object": None}), 200

        return jsonify({
            "message": "No shops found",
            "object": None
        }), 200

    # populate the object to a list of dictionary object
    for obj in query:
        data.append(obj.format())
    return jsonify({
        "message": "All sanctioned shops",
        "object": data
    }), 200
